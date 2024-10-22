import time
import json
import requests
import torch
import bittensor as bt
from template.base.validator import BaseValidatorNeuron
from template.protocol import TrainingProtocol

class TrainingValidator(BaseValidatorNeuron):
    def __init__(self, config=None, central_repo: str = "Tobius/yogpt_test"):
        super().__init__(config=config)
        
        self.central_repo = central_repo  # Central repository URL

    def read_commits(self):
        """Read commits from the central repository."""
        # Implementation to read commits from the repository
        commits = self.fetch_commits_from_repository()
        return commits

    def group_commits(self, commits):
        """Group commits by job."""
        job_groups = {}
        for commit in commits:
            job_id = commit.get("metrics", {}).get("job_id")
            if job_id not in job_groups:
                job_groups[job_id] = []
            job_groups[job_id].append(commit)
        return job_groups

    def load_and_evaluate(self, job_groups):
        """Load and evaluate each job."""
        for job_id, commits in job_groups.items():
            metrics_list = self.extract_metrics_by_job_id(commits, job_id)
            if metrics_list:
                self.score_miners(metrics_list, job_id)
                self.mark_job_as_done(job_id)

    def verify_losses(self, metrics_list):
        """Assess and verify the losses for each task."""
        # Implementation to verify losses
        for metric in metrics_list:
            if not self.is_loss_verified(metric):
                continue  # Skip if loss is not verified
            self.update_scores(torch.tensor([1.0]), [metric["miner_uid"]])

    def reward_best_miner(self, job_id):
        """Reward the miner with the best performance for each job."""
        metrics_list = self.get_metrics_for_job(job_id)
        if metrics_list:
            lowest_loss_commit = min(metrics_list, key=lambda x: x["final_loss"])
            self.update_scores(torch.tensor([1.0]), [lowest_loss_commit["miner_uid"]])

    def mark_job_as_done(self, job_id):
        """Mark the evaluated job as complete."""
        # Implementation to mark the job as done
        self.update_job_status(job_id, status="done")

    def filter_jobs(self, job_groups):
        """Filter and process only unscored jobs."""
        unscored_jobs = {job_id: commits for job_id, commits in job_groups.items() if not self.is_job_scored(job_id)}
        return unscored_jobs

    def evaluate_jobs(self):
        """Main method to evaluate jobs."""
        commits = self.read_commits()
        job_groups = self.group_commits(commits)
        unscored_jobs = self.filter_jobs(job_groups)
        self.load_and_evaluate(unscored_jobs)

    async def forward(self):
        """Main execution method."""
        try:
            commits = self.fetch_commits()
            job_groups = self.group_commits_by_job(commits)
            self.evaluate_jobs(job_groups)
        except Exception as e:
            bt.logging.error(f"Error in forward: {str(e)}")

# Main execution
if __name__ == "__main__":
    import asyncio  # Import asyncio to run the async function
    async def main():
        async with TrainingValidator() as validator:
            while True:
                bt.logging.info(f"Validator running... {time.time()}")
                await validator.forward()  # Ensure async function is called properly
                await asyncio.sleep(5)  # Use asyncio.sleep instead of time.sleep

    asyncio.run(main())  # Run the main async function
