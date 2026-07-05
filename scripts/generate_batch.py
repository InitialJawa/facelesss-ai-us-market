#!/usr/bin/env python3
"""Generate 10 videos for US market faceless content."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.queue import PipelineQueue
from pipeline.orchestrator import PipelineOrchestrator
from brain.manager import Brain
from app.config import settings
from loguru import logger

TOPICS = [
    "Why Elon Musk is Betting Big on AI in 2026",
    "The Rise of Faceless YouTube Channels Making Millions",
    "How to Start a Faceless Channel in 2026 (Step by Step)",
    "5 AI Tools That Will Replace Your Entire Workflow",
    "The Truth About Making Money Online in 2026",
    "Why Your Faceless Channel is NOT Growing (And How to Fix It)",
    "10,000 Hours of AI Content: What I Learned",
    "The Future of Digital Marketing: AI Content Automation",
    "How AI is Changing Hollywood Forever",
    "Passive Income with AI: The Complete Blueprint",
]

TOPICS_2 = [
    "How I Made $10,000 With AI Videos (Full Guide)",
    "The Psychology of Viral Faceless Content",
    "5 Niche Ideas for Faceless YouTube Channels in 2026",
    "Why Most Faceless Channels FAIL (And How to WIN)",
    "AI Voiceover: The Best Text-to-Speech for YouTube",
    "How to Edit Faceless Videos in 5 Minutes",
    "The Secret Algorithm Hack for Faceless Channels",
    "Top 10 AI Tools for Content Creators in 2026",
    "How to Research Viral Topics for Faceless Videos",
    "From Zero to 100K Subs: Faceless Channel Strategy",
]


async def main():
    logger.info("=" * 60)
    logger.info("FACELess AI - Batch Generator (US Market)")
    logger.info("=" * 60)

    brain = Brain(settings.brain_dir)
    brain.load()

    queue = PipelineQueue(settings.queue_db_path)
    queue.resume_all()

    orchestrator = PipelineOrchestrator(brain, queue)

    for i, topic in enumerate(TOPICS, 1):
        job_id = orchestrator.create_job(topic, niche="AI content creation")
        logger.info(f"[{i}/10] Job created: {job_id[:8]} - {topic[:60]}...")

    logger.info(f"\n{'='*60}")
    logger.info(f"10 jobs enqueued. Processing now...")
    logger.info(f"{'='*60}")

    results = await orchestrator.process_pending(limit=10)

    logger.info(f"\n{'='*60}")
    logger.info(f"RESULTS:")
    logger.info(f"{'='*60}")

    for job_id, success in results:
        job = queue.get_job(job_id)
        status = "✅ SUCCESS" if success else "❌ FAILED"
        stage = job["stage"] if job else "unknown"
        topic = job["topic"][:60] if job else "unknown"
        logger.info(f"  {status} | {stage:15s} | {topic}")

    logger.info(f"\nOutput directory: {os.path.abspath(settings.output_dir)}")
    logger.info(f"Voices directory: {os.path.abspath(settings.voices_dir)}")

    output_files = []
    for f in os.listdir(settings.output_dir):
        if f.endswith(".mp4"):
            output_files.append(f)
    logger.info(f"Videos generated: {len(output_files)}")
    for f in sorted(output_files):
        size = os.path.getsize(os.path.join(settings.output_dir, f))
        logger.info(f"  📹 {f} ({size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    asyncio.run(main())
