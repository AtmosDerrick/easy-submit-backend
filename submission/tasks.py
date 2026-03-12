import random
import logging
from .models import Submission

logger = logging.getLogger(__name__)


def score_submission(submission_id: str):
    """
    Simulates plagiarism and AI detection scoring for a submission.
    Runs in a Django-Q2 background worker — never in the request cycle.

    Replace the random values with real API calls when ready, 
    everything else stays the same.
    """
    try:
        submission = Submission.objects.get(pk=submission_id)
    except Submission.DoesNotExist:
        logger.warning(f"score_submission: submission {submission_id} not found, likely withdrawn.")
        return

    plagiarism_score = round(random.uniform(0, 100), 2)
    ai_score = round(random.uniform(0, 100), 2)

    submission.plagiarism_score = plagiarism_score
    submission.ai_score = ai_score
    submission.save(update_fields=['plagiarism_score', 'ai_score', 'updated_at'])

    logger.info(
        f"score_submission: submission {submission_id} scored — "
        f"plagiarism={plagiarism_score}, ai={ai_score}"
    )