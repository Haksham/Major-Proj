#!/usr/bin/env python3
"""
SALF Seed Data Script
Populates the database with realistic dummy data.

Usage (from backend/ directory):
    python seed_data.py
"""
import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.database import (
    User, UserRole, Designation,
    Institution, Department,
    Contribution, ContributionCategory, ContributionStatus,
)

# ── Deterministic fake Ethereum wallets (42-char) ─────────────────────────────
W = {
    "inst_admin": "0xAa00000000000000000000000000000000000001",
    "hod_cse":    "0xBb00000000000000000000000000000000000002",
    "hod_ece":    "0xCc00000000000000000000000000000000000003",
    "f1":         "0xDd00000000000000000000000000000000000004",  # Dr. Amit Sharma
    "f2":         "0xEe00000000000000000000000000000000000005",  # Dr. Priya Patel
    "f3":         "0xFF00000000000000000000000000000000000006",  # Dr. Rahul Verma
    "f4":         "0xaa00000000000000000000000000000000000007",  # Dr. Sneha Gupta
    "f5":         "0xBB00000000000000000000000000000000000008",  # Dr. Vikram Singh
    "f6":         "0xcc00000000000000000000000000000000000009",  # Dr. Anita Desai
}


def _eval_details(quality: float, novelty: float, summary: str) -> str:
    return json.dumps({
        "quality_score": quality,
        "novelty_percentage": novelty,
        "summary": summary,
        "strengths": ["Clear methodology", "Well-structured abstract"],
        "concerns": ["Could expand on limitations"],
        "evaluation_version": "seed-mock",
    })


def _credits(base: float, quality: float, novelty: float) -> float:
    return round(base * (1 + quality / 100) * (1 + novelty / 200), 2)


async def _get_or_skip(session, model, wallet_key: str, label: str, **kwargs):
    """Insert a User if their wallet is not in the DB; return the user."""
    existing = (await session.execute(
        select(model).where(model.wallet_address == W[wallet_key])
    )).scalar_one_or_none()
    if existing is not None:
        print(f"  → already exists: {label}")
        return existing
    obj = model(wallet_address=W[wallet_key], **kwargs)
    session.add(obj)
    await session.flush()
    print(f"  ✓ created: {label}")
    return obj


async def seed():
    async with AsyncSessionLocal() as session:

        # ── 1. Institution ────────────────────────────────────────────────────
        print("\n[Institution]")
        inst = (await session.execute(
            select(Institution).where(Institution.code == "NITECH")
        )).scalar_one_or_none()

        if inst is None:
            inst = Institution(
                code="NITECH",
                name="National Institute of Technology",
                admin_address=W["inst_admin"],
                is_active=True,
                created_at=datetime.utcnow(),
            )
            session.add(inst)
            await session.flush()
            print("  ✓ created: NITECH – National Institute of Technology")
        else:
            print("  → already exists: NITECH")

        # ── 2. Departments (pre-create without hod_id) ────────────────────────
        print("\n[Departments]")

        async def get_or_create_dept(code, name):
            d = (await session.execute(
                select(Department).where(
                    Department.institution_id == inst.id,
                    Department.code == code,
                )
            )).scalar_one_or_none()
            if d is None:
                d = Department(
                    institution_id=inst.id,
                    code=code,
                    name=name,
                    is_active=True,
                    created_at=datetime.utcnow(),
                )
                session.add(d)
                await session.flush()
                print(f"  ✓ created: {code} – {name}")
            else:
                print(f"  → already exists: {code}")
            return d

        cse = await get_or_create_dept("CSE",  "Computer Science & Engineering")
        ece = await get_or_create_dept("ECE",  "Electronics & Communication Engineering")
        await get_or_create_dept("MECH", "Mechanical Engineering")

        # ── 3. Institute Admin ────────────────────────────────────────────────
        print("\n[Institute Admin]")
        inst_admin = await _get_or_skip(
            session, User, "inst_admin", "Institute Admin",
            employee_id="IA001",
            name="Institute Admin",
            email="iadmin@nitech.edu",
            role=UserRole.INSTITUTE_ADMIN,
            institution_id=inst.id,
            designation=Designation.PROFESSOR,
            is_active=True,
            total_credits=0.0,
            created_at=datetime.utcnow(),
        )
        inst.admin_address = inst_admin.wallet_address

        # ── 4. HoDs ───────────────────────────────────────────────────────────
        print("\n[Heads of Department]")
        hod_cse = await _get_or_skip(
            session, User, "hod_cse", "HOD-CSE",
            employee_id="HOD001",
            name="HOD-CSE",
            email="hod.cse@nitech.edu",
            role=UserRole.HOD,
            institution_id=inst.id,
            department_id=cse.id,
            designation=Designation.PROFESSOR,
            is_active=True,
            total_credits=0.0,
            created_at=datetime.utcnow(),
        )
        # Always sync name + dept link
        hod_cse.name = "HOD-CSE"
        cse.hod_id = hod_cse.id

        hod_ece = await _get_or_skip(
            session, User, "hod_ece", "HOD-ECE",
            employee_id="HOD002",
            name="HOD-ECE",
            email="hod.ece@nitech.edu",
            role=UserRole.HOD,
            institution_id=inst.id,
            department_id=ece.id,
            designation=Designation.PROFESSOR,
            is_active=True,
            total_credits=0.0,
            created_at=datetime.utcnow(),
        )
        ece.hod_id = hod_ece.id

        # ── 5. Update any OTHER existing HOD in CSE to HOD-CSE ───────────────
        existing_cse_hods = (await session.execute(
            select(User).where(
                User.role == UserRole.HOD,
                User.department_id == cse.id,
                User.wallet_address != W["hod_cse"],
            )
        )).scalars().all()
        for h in existing_cse_hods:
            h.name = "HOD-CSE"
            print(f"  → renamed existing HOD (wallet {h.wallet_address[:10]}…) → HOD-CSE")

        # ── 6. Faculty (CSE) ──────────────────────────────────────────────────
        print("\n[CSE Faculty]")
        f1 = await _get_or_skip(
            session, User, "f1", "Dr. Amit Sharma",
            employee_id="FAC001", name="Dr. Amit Sharma",
            email="amit.sharma@nitech.edu",
            role=UserRole.FACULTY, institution_id=inst.id,
            department_id=cse.id, designation=Designation.PROFESSOR,
            is_active=True, total_credits=0.0, created_at=datetime.utcnow(),
        )
        f2 = await _get_or_skip(
            session, User, "f2", "Dr. Priya Patel",
            employee_id="FAC002", name="Dr. Priya Patel",
            email="priya.patel@nitech.edu",
            role=UserRole.FACULTY, institution_id=inst.id,
            department_id=cse.id, designation=Designation.ASSOCIATE_PROFESSOR,
            is_active=True, total_credits=0.0, created_at=datetime.utcnow(),
        )
        f3 = await _get_or_skip(
            session, User, "f3", "Dr. Rahul Verma",
            employee_id="FAC003", name="Dr. Rahul Verma",
            email="rahul.verma@nitech.edu",
            role=UserRole.FACULTY, institution_id=inst.id,
            department_id=cse.id, designation=Designation.ASSISTANT_PROFESSOR,
            is_active=True, total_credits=0.0, created_at=datetime.utcnow(),
        )
        f4 = await _get_or_skip(
            session, User, "f4", "Dr. Sneha Gupta",
            employee_id="FAC004", name="Dr. Sneha Gupta",
            email="sneha.gupta@nitech.edu",
            role=UserRole.FACULTY, institution_id=inst.id,
            department_id=cse.id, designation=Designation.ASSOCIATE_PROFESSOR,
            is_active=True, total_credits=0.0, created_at=datetime.utcnow(),
        )

        # ── 7. Faculty (ECE) ──────────────────────────────────────────────────
        print("\n[ECE Faculty]")
        f5 = await _get_or_skip(
            session, User, "f5", "Dr. Vikram Singh",
            employee_id="FAC005", name="Dr. Vikram Singh",
            email="vikram.singh@nitech.edu",
            role=UserRole.FACULTY, institution_id=inst.id,
            department_id=ece.id, designation=Designation.PROFESSOR,
            is_active=True, total_credits=0.0, created_at=datetime.utcnow(),
        )
        f6 = await _get_or_skip(
            session, User, "f6", "Dr. Anita Desai",
            employee_id="FAC006", name="Dr. Anita Desai",
            email="anita.desai@nitech.edu",
            role=UserRole.FACULTY, institution_id=inst.id,
            department_id=ece.id, designation=Designation.ASSOCIATE_PROFESSOR,
            is_active=True, total_credits=0.0, created_at=datetime.utcnow(),
        )

        await session.commit()

        # ── Re-fetch IDs after commit ─────────────────────────────────────────
        for obj in [hod_cse, hod_ece, f1, f2, f3, f4, f5, f6, cse, ece]:
            await session.refresh(obj)

        # ── 8. Contributions ──────────────────────────────────────────────────
        print("\n[Contributions]")

        async def contribution_exists(ipfs_hash: str) -> bool:
            r = (await session.execute(
                select(Contribution).where(Contribution.ipfs_hash == ipfs_hash)
            )).scalar_one_or_none()
            return r is not None

        now = datetime.utcnow()

        contributions_spec = [
            # ── Dr. Amit Sharma (CSE) ── f1 ──────────────────────────────────
            dict(
                ipfs_hash="QmSeedAmit001DeepLearningMedical00000000000000",
                metadata_hash="0xSeedMeta001A0000000000000000000000000000001",
                faculty=f1, category=ContributionCategory.REFEREED_JOURNAL,
                title="Deep Learning for Medical Image Segmentation Using U-Net",
                abstract=(
                    "This paper presents a novel deep learning framework leveraging U-Net "
                    "architecture for automated medical image segmentation in MRI scans. "
                    "We introduce a new attention mechanism that improves segmentation "
                    "accuracy by 12% over baselines on the BraTS 2023 dataset. Extensive "
                    "experiments on three public benchmarks confirm the robustness and "
                    "clinical applicability of the proposed approach."
                ),
                journal_name="IEEE Transactions on Medical Imaging",
                doi="10.1109/TMI.2024.001",
                publication_date=now - timedelta(days=90),
                co_authors="Dr. R. Patel, Dr. S. Kumar",
                status=ContributionStatus.VALIDATED,
                ai_quality_score=82.0, novelty_percentage=75.0,
                base_credits=25.0,
                reviewer=hod_cse,
                review_notes="Excellent contribution with strong experimental evidence.",
                review_time=now - timedelta(days=60),
                submission_time=now - timedelta(days=85),
                blockchain_id=1001,
                blockchain_tx_hash="0xSeedTx001A000000000000000000000000000000001",
            ),
            dict(
                ipfs_hash="QmSeedAmit002QuantumCrypto000000000000000000000",
                metadata_hash="0xSeedMeta002A0000000000000000000000000000002",
                faculty=f1, category=ContributionCategory.RESEARCH_PROJECT,
                title="Quantum Computing Applications in Post-Quantum Cryptography",
                abstract=(
                    "This research project explores the practical applications of quantum "
                    "computing algorithms (Shor's and Grover's) in breaking and designing "
                    "cryptographic primitives. We develop a novel hybrid classical-quantum "
                    "framework for lattice-based encryption that achieves NIST post-quantum "
                    "standards while maintaining computational efficiency on NISQ devices."
                ),
                journal_name=None, doi=None,
                publication_date=now - timedelta(days=180),
                co_authors="Dr. P. Mehta",
                status=ContributionStatus.VALIDATED,
                ai_quality_score=78.0, novelty_percentage=68.0,
                base_credits=20.0,
                reviewer=hod_cse,
                review_notes="Strong theoretical foundation. Approved.",
                review_time=now - timedelta(days=150),
                submission_time=now - timedelta(days=175),
                blockchain_id=1002,
                blockchain_tx_hash="0xSeedTx002A000000000000000000000000000000002",
            ),
            dict(
                ipfs_hash="QmSeedAmit003NeuralNetworksBook000000000000000",
                metadata_hash="0xSeedMeta003A0000000000000000000000000000003",
                faculty=f1, category=ContributionCategory.BOOK_CHAPTER,
                title="Introduction to Convolutional Neural Networks: A Practical Guide",
                abstract=(
                    "This book chapter provides a comprehensive introduction to convolutional "
                    "neural networks (CNNs), covering architectural fundamentals, training "
                    "techniques, and real-world applications in computer vision. The chapter "
                    "includes practical implementation examples using PyTorch."
                ),
                isbn="978-0-123-45678-9",
                publication_date=None,
                co_authors=None,
                status=ContributionStatus.PENDING,
                ai_quality_score=0.0, novelty_percentage=0.0, base_credits=5.0,
                reviewer=None, review_notes=None, review_time=None,
                submission_time=now - timedelta(days=5),
                blockchain_id=None, blockchain_tx_hash=None,
            ),

            # ── Dr. Priya Patel (CSE) ── f2 ──────────────────────────────────
            dict(
                ipfs_hash="QmSeedPriya001EdgeComputingSmartCities000000000",
                metadata_hash="0xSeedMeta001B0000000000000000000000000000004",
                faculty=f2, category=ContributionCategory.NATIONAL_CONFERENCE,
                title="Edge Computing Architecture for Real-Time Smart City Traffic Management",
                abstract=(
                    "We propose a distributed edge computing framework for real-time traffic "
                    "management in smart cities. The system integrates IoT sensor data with "
                    "federated machine learning models deployed at edge nodes, reducing "
                    "latency by 68% compared to cloud-only solutions while preserving privacy."
                ),
                journal_name="Proc. IEEE INDICON 2024",
                doi=None,
                publication_date=now - timedelta(days=30),
                co_authors="Dr. A. Sharma, Mr. R. Iyer",
                status=ContributionStatus.UNDER_REVIEW,
                ai_quality_score=71.0, novelty_percentage=62.0,
                base_credits=10.0,
                reviewer=hod_cse,
                review_notes=None, review_time=None,
                submission_time=now - timedelta(days=20),
                blockchain_id=1003,
                blockchain_tx_hash="0xSeedTx003B000000000000000000000000000000003",
            ),
            dict(
                ipfs_hash="QmSeedPriya002BlockchainHealthcare000000000000",
                metadata_hash="0xSeedMeta002B0000000000000000000000000000005",
                faculty=f2, category=ContributionCategory.REFEREED_JOURNAL,
                title="Blockchain-Based Data Integrity Framework for Healthcare Records",
                abstract=(
                    "Electronic health records suffer from integrity and privacy vulnerabilities. "
                    "This paper introduces a permissioned blockchain solution using Hyperledger "
                    "Fabric to ensure tamper-proof storage of patient data. We demonstrate "
                    "our system achieves 99.97% integrity with sub-second query latency across "
                    "a network of 50 simulated hospitals."
                ),
                issn="1234-5678",
                doi=None,
                publication_date=None,
                co_authors=None,
                status=ContributionStatus.PENDING,
                ai_quality_score=0.0, novelty_percentage=0.0, base_credits=25.0,
                reviewer=None, review_notes=None, review_time=None,
                submission_time=now - timedelta(days=3),
                blockchain_id=None, blockchain_tx_hash=None,
            ),

            # ── Dr. Rahul Verma (CSE) ── f3 ──────────────────────────────────
            dict(
                ipfs_hash="QmSeedRahul001PatentGraphColoring0000000000000",
                metadata_hash="0xSeedMeta001C0000000000000000000000000000006",
                faculty=f3, category=ContributionCategory.PATENT_FILED,
                title="System and Method for Parallel Graph Coloring Using GPU Acceleration",
                abstract=(
                    "A novel parallel algorithm for graph coloring problems exploiting GPU "
                    "SIMT architecture. The invention achieves O(log n) coloring on sparse "
                    "graphs using a greedy independent-set approach with conflict resolution, "
                    "yielding 40x speedup over CPU baselines on real-world social network graphs."
                ),
                publication_date=None, co_authors="Dr. S. Nair",
                status=ContributionStatus.PENDING,
                ai_quality_score=0.0, novelty_percentage=0.0, base_credits=15.0,
                reviewer=None, review_notes=None, review_time=None,
                submission_time=now - timedelta(days=2),
                blockchain_id=None, blockchain_tx_hash=None,
            ),
            dict(
                ipfs_hash="QmSeedRahul002DistributedSystemsBook00000000000",
                metadata_hash="0xSeedMeta002C0000000000000000000000000000007",
                faculty=f3, category=ContributionCategory.NATIONAL_BOOK,
                title="Distributed Systems and Cloud Computing: Fundamentals",
                abstract=(
                    "An introductory textbook covering distributed system principles including "
                    "consensus algorithms, fault tolerance, and cloud infrastructure. The text "
                    "is aimed at undergraduate students and provides exercises and case studies."
                ),
                isbn="978-0-987-65432-1",
                publication_date=now - timedelta(days=200),
                co_authors=None,
                status=ContributionStatus.REJECTED,
                ai_quality_score=45.0, novelty_percentage=30.0, base_credits=20.0,
                reviewer=hod_cse,
                review_notes="Abstract lacks sufficient novelty and original research contribution. Please revise.",
                review_time=now - timedelta(days=180),
                submission_time=now - timedelta(days=195),
                blockchain_id=1004,
                blockchain_tx_hash="0xSeedTx004C000000000000000000000000000000004",
            ),

            # ── Dr. Sneha Gupta (CSE) ── f4 ──────────────────────────────────
            dict(
                ipfs_hash="QmSeedSneha001AIEthicsFlagged000000000000000000",
                metadata_hash="0xSeedMeta001D0000000000000000000000000000008",
                faculty=f4, category=ContributionCategory.REFEREED_JOURNAL,
                title="AI Ethics and Algorithmic Fairness in Machine Learning Systems",
                abstract=(
                    "This novel study investigates bias and fairness in machine learning "
                    "models deployed in hiring and loan approval systems. We propose an "
                    "innovative fairness-aware regularization technique that reduces "
                    "demographic parity gaps by 35% with minimal accuracy trade-off."
                ),
                issn="9876-5432",
                doi="10.1109/TNNLS.2024.002",
                publication_date=now - timedelta(days=45),
                co_authors="Dr. A. Sharma",
                status=ContributionStatus.FLAGGED,
                ai_quality_score=55.0, novelty_percentage=48.0, base_credits=25.0,
                reviewer=hod_cse,
                review_notes="Flagged: high similarity to existing literature (potential duplicate).",
                review_time=now - timedelta(days=30),
                is_flagged=True,
                flag_reason="Cosine similarity > 0.85 with existing contribution ID #1001",
                fraud_score=0.88,
                fraud_reasons=json.dumps(["high_similarity_detected", "abstract_overlap"]),
                submission_time=now - timedelta(days=40),
                blockchain_id=1005,
                blockchain_tx_hash="0xSeedTx005D000000000000000000000000000000005",
            ),
            dict(
                ipfs_hash="QmSeedSneha002SortingAlgorithmsConf0000000000",
                metadata_hash="0xSeedMeta002D0000000000000000000000000000009",
                faculty=f4, category=ContributionCategory.NATIONAL_CONFERENCE,
                title="Empirical Comparison of Adaptive Sorting Algorithms on GPU Architectures",
                abstract=(
                    "This paper presents a systematic empirical evaluation of adaptive sorting "
                    "algorithms (TimSort, IntroSort, pdqsort) on modern GPU architectures. "
                    "Benchmarks on NVIDIA A100 show pdqsort achieves 2.3x throughput over "
                    "TimSort for partially-sorted datasets exceeding 10M elements."
                ),
                journal_name="Proc. NCC 2024",
                doi=None,
                publication_date=now - timedelta(days=120),
                co_authors="Mr. K. Reddy",
                status=ContributionStatus.VALIDATED,
                ai_quality_score=65.0, novelty_percentage=55.0,
                base_credits=10.0,
                reviewer=hod_cse,
                review_notes="Good empirical study. Approved.",
                review_time=now - timedelta(days=100),
                submission_time=now - timedelta(days=115),
                blockchain_id=1006,
                blockchain_tx_hash="0xSeedTx006D000000000000000000000000000000006",
            ),

            # ── Dr. Vikram Singh (ECE) ── f5 ──────────────────────────────────
            dict(
                ipfs_hash="QmSeedVikram001VLSI5GComms0000000000000000000",
                metadata_hash="0xSeedMeta001E000000000000000000000000000000A",
                faculty=f5, category=ContributionCategory.REFEREED_JOURNAL,
                title="VLSI Design Optimization for 5G mmWave Communication Front-Ends",
                abstract=(
                    "This paper introduces a novel VLSI design methodology for 5G millimeter-"
                    "wave front-end circuits, targeting 28 GHz and 39 GHz bands. Our "
                    "automated layout optimization reduces chip area by 22% and improves "
                    "noise figure by 1.8 dB compared to manual designs using 7nm TSMC process."
                ),
                journal_name="IEEE Journal of Solid-State Circuits",
                doi="10.1109/JSSC.2024.003",
                publication_date=now - timedelta(days=70),
                co_authors="Dr. P. Nair",
                status=ContributionStatus.VALIDATED,
                ai_quality_score=80.0, novelty_percentage=72.0,
                base_credits=25.0,
                reviewer=hod_ece,
                review_notes="Excellent work on mmWave design. Approved.",
                review_time=now - timedelta(days=50),
                submission_time=now - timedelta(days=65),
                blockchain_id=1007,
                blockchain_tx_hash="0xSeedTx007E000000000000000000000000000000007",
            ),
            dict(
                ipfs_hash="QmSeedVikram002AntennaIoT0000000000000000000000",
                metadata_hash="0xSeedMeta002E000000000000000000000000000000B",
                faculty=f5, category=ContributionCategory.RESEARCH_PROJECT,
                title="Reconfigurable Antenna Design for Multi-Band IoT Applications",
                abstract=(
                    "We present a novel reconfigurable microstrip patch antenna that operates "
                    "across NB-IoT, LoRa, and Zigbee frequency bands using PIN diode switching. "
                    "The prototype achieves -15 dB return loss with 85% radiation efficiency "
                    "across all three bands, validated via full-wave EM simulation and measurement."
                ),
                doi=None,
                publication_date=now - timedelta(days=15),
                co_authors="Dr. A. Desai, Mr. T. Shah",
                status=ContributionStatus.UNDER_REVIEW,
                ai_quality_score=74.0, novelty_percentage=65.0,
                base_credits=20.0,
                reviewer=hod_ece,
                review_notes=None, review_time=None,
                submission_time=now - timedelta(days=10),
                blockchain_id=1008,
                blockchain_tx_hash="0xSeedTx008E000000000000000000000000000000008",
            ),

            # ── Dr. Anita Desai (ECE) ── f6 ──────────────────────────────────
            dict(
                ipfs_hash="QmSeedAnita001EnergyMonitor0000000000000000000",
                metadata_hash="0xSeedMeta001F000000000000000000000000000000C",
                faculty=f6, category=ContributionCategory.NATIONAL_CONFERENCE,
                title="IoT-Based Non-Intrusive Energy Monitoring System for Smart Buildings",
                abstract=(
                    "This paper presents a low-cost IoT energy monitoring system using "
                    "current transformers and a microcontroller-based edge node for "
                    "non-intrusive load monitoring (NILM) in smart buildings. The system "
                    "identifies individual appliance consumption with 91% accuracy using "
                    "a lightweight CNN deployed on ESP32."
                ),
                journal_name="Proc. ICPEICES 2024",
                doi=None,
                publication_date=now - timedelta(days=100),
                co_authors="Dr. V. Singh",
                status=ContributionStatus.VALIDATED,
                ai_quality_score=69.0, novelty_percentage=58.0,
                base_credits=10.0,
                reviewer=hod_ece,
                review_notes="Solid practical contribution. Approved.",
                review_time=now - timedelta(days=80),
                submission_time=now - timedelta(days=95),
                blockchain_id=1009,
                blockchain_tx_hash="0xSeedTx009F000000000000000000000000000000009",
            ),
            dict(
                ipfs_hash="QmSeedAnita002EmbeddedWorkshop00000000000000000",
                metadata_hash="0xSeedMeta002F000000000000000000000000000000D",
                faculty=f6, category=ContributionCategory.INTERNATIONAL_LECTURE,
                title="Invited Lecture: Embedded AI on Edge Devices – Challenges and Solutions",
                abstract=(
                    "An invited lecture delivered at the International Workshop on Embedded "
                    "Intelligence (IWEI 2024, Singapore) covering deployment strategies for "
                    "neural network inference on resource-constrained microcontrollers, "
                    "including quantization, pruning, and knowledge distillation techniques."
                ),
                publication_date=None, co_authors=None,
                status=ContributionStatus.PENDING,
                ai_quality_score=0.0, novelty_percentage=0.0, base_credits=7.0,
                reviewer=None, review_notes=None, review_time=None,
                submission_time=now - timedelta(days=1),
                blockchain_id=None, blockchain_tx_hash=None,
            ),
        ]

        total_credits_map: dict = {}

        for spec in contributions_spec:
            ipfs = spec["ipfs_hash"]
            if await contribution_exists(ipfs):
                print(f"  → skip (exists): {spec['title'][:55]}…")
                continue

            base = spec["base_credits"]
            quality = spec.get("ai_quality_score", 0.0)
            novelty = spec.get("novelty_percentage", 0.0)
            final = _credits(base, quality, novelty) if spec["status"] == ContributionStatus.VALIDATED else 0.0

            fac: User = spec["faculty"]
            rev: User | None = spec.get("reviewer")

            eval_details = None
            if quality > 0:
                eval_details = _eval_details(quality, novelty, f"Evaluation of: {spec['title'][:60]}")

            c = Contribution(
                ipfs_hash=ipfs,
                metadata_hash=spec["metadata_hash"],
                faculty_id=fac.id,
                faculty_address=fac.wallet_address,
                category=spec["category"],
                title=spec["title"],
                abstract=spec["abstract"],
                file_name=f"seed_{fac.employee_id}_{spec['category'].value}.pdf",
                file_size=250_000,

                journal_name=spec.get("journal_name"),
                isbn=spec.get("isbn"),
                issn=spec.get("issn"),
                doi=spec.get("doi"),
                publication_date=spec.get("publication_date"),
                co_authors=spec.get("co_authors"),

                status=spec["status"],
                ai_quality_score=quality,
                novelty_percentage=novelty,
                base_credits=base,
                final_credits=final,
                calculated_credits=_credits(base, quality, novelty) if quality > 0 else base,
                evaluation_details=eval_details,

                reviewer_id=rev.id if rev else None,
                review_notes=spec.get("review_notes"),
                review_time=spec.get("review_time"),

                is_flagged=spec.get("is_flagged", False),
                flag_reason=spec.get("flag_reason"),
                fraud_score=spec.get("fraud_score", 0.0),
                fraud_reasons=spec.get("fraud_reasons"),

                submission_time=spec.get("submission_time", now),
                blockchain_id=spec.get("blockchain_id"),
                blockchain_tx_hash=spec.get("blockchain_tx_hash"),
                created_at=spec.get("submission_time", now),
            )
            session.add(c)

            if spec["status"] == ContributionStatus.VALIDATED:
                total_credits_map[fac.id] = total_credits_map.get(fac.id, 0.0) + final

            print(f"  ✓ {spec['status'].value:12s}  {spec['title'][:55]}…")

        await session.flush()

        # ── 9. Update faculty total_credits ───────────────────────────────────
        print("\n[Updating total_credits]")
        for uid, credits in total_credits_map.items():
            u = (await session.execute(select(User).where(User.id == uid))).scalar_one()
            u.total_credits = round(credits, 2)
            print(f"  ✓ {u.name}: {u.total_credits} credits")

        await session.commit()
        print("\n✅  Seed complete.\n")


# ── Wallets for IITB ──────────────────────────────────────────────────────────
W2 = {
    "admin":   "0xAa00000000000000000000000000000000000010",
    "hod_cs":  "0xBb00000000000000000000000000000000000011",
    "hod_me":  "0xCc00000000000000000000000000000000000012",
    "hod_ee":  "0xDd00000000000000000000000000000000000013",
    "fi1":     "0xEe00000000000000000000000000000000000014",
    "fi2":     "0xFF00000000000000000000000000000000000015",
    "fi3":     "0xaa00000000000000000000000000000000000016",
    "fi4":     "0xBB00000000000000000000000000000000000017",
    "fi5":     "0xcc00000000000000000000000000000000000018",
    "fi6":     "0xDD00000000000000000000000000000000000019",
    "fi7":     "0xee00000000000000000000000000000000000020",
}

# ── Wallets for RVCE ──────────────────────────────────────────────────────────
W3 = {
    "admin":      "0xAa00000000000000000000000000000000000021",
    "hod_it":     "0xBb00000000000000000000000000000000000022",
    "hod_civil":  "0xCc00000000000000000000000000000000000023",
    "fr1":        "0xDd00000000000000000000000000000000000024",
    "fr2":        "0xEe00000000000000000000000000000000000025",
    "fr3":        "0xFF00000000000000000000000000000000000026",
    "fr4":        "0xaa00000000000000000000000000000000000027",
    "fr5":        "0xBB00000000000000000000000000000000000028",
}


async def seed_extra():
    """Seed IITB and RVCE institutions with departments, HODs, faculty, and contributions."""

    async with AsyncSessionLocal() as session:

        async def upsert_inst(code, name, admin_wallet):
            inst = (await session.execute(
                select(Institution).where(Institution.code == code)
            )).scalar_one_or_none()
            if inst is None:
                inst = Institution(code=code, name=name, admin_address=admin_wallet,
                                   is_active=True, created_at=datetime.utcnow())
                session.add(inst)
                await session.flush()
                print(f"  ✓ created: {code} – {name}")
            else:
                print(f"  → already exists: {code}")
            return inst

        async def upsert_dept(inst_id, code, name):
            d = (await session.execute(
                select(Department).where(Department.institution_id == inst_id,
                                         Department.code == code)
            )).scalar_one_or_none()
            if d is None:
                d = Department(institution_id=inst_id, code=code, name=name,
                               is_active=True, created_at=datetime.utcnow())
                session.add(d)
                await session.flush()
                print(f"  ✓ dept: {code}")
            else:
                print(f"  → dept exists: {code}")
            return d

        async def upsert_user(wallet, **kwargs):
            u = (await session.execute(
                select(User).where(User.wallet_address == wallet)
            )).scalar_one_or_none()
            if u is None:
                u = User(wallet_address=wallet, **kwargs,
                         is_active=True, total_credits=0.0,
                         created_at=datetime.utcnow())
                session.add(u)
                await session.flush()
                print(f"  ✓ user: {kwargs['name']}")
            else:
                print(f"  → user exists: {kwargs['name']}")
            return u

        async def contrib_exists(ipfs_hash):
            return (await session.execute(
                select(Contribution).where(Contribution.ipfs_hash == ipfs_hash)
            )).scalar_one_or_none() is not None

        now = datetime.utcnow()

        # ════════════════════════════════════════════════════════════════════════
        # INSTITUTION 2 — IIT Bombay
        # ════════════════════════════════════════════════════════════════════════
        print("\n[IIT Bombay]")
        iitb = await upsert_inst("IITB", "Indian Institute of Technology Bombay", W2["admin"])

        print("\n[IITB Departments]")
        cs   = await upsert_dept(iitb.id, "CS",   "Computer Science")
        me   = await upsert_dept(iitb.id, "ME",   "Mechanical Engineering")
        ee   = await upsert_dept(iitb.id, "EE",   "Electrical Engineering")

        print("\n[IITB Institute Admin]")
        iitb_ia = await upsert_user(W2["admin"],
            employee_id="IITB-IA01", name="IITB Institute Admin",
            email="iadmin@iitb.ac.in", role=UserRole.INSTITUTE_ADMIN,
            institution_id=iitb.id, designation=Designation.PROFESSOR)
        iitb.admin_address = iitb_ia.wallet_address

        print("\n[IITB HoDs]")
        hod_cs = await upsert_user(W2["hod_cs"],
            employee_id="IITB-H01", name="HOD-CS",
            email="hod.cs@iitb.ac.in", role=UserRole.HOD,
            institution_id=iitb.id, department_id=cs.id,
            designation=Designation.PROFESSOR)
        cs.hod_id = hod_cs.id

        hod_me = await upsert_user(W2["hod_me"],
            employee_id="IITB-H02", name="HOD-ME",
            email="hod.me@iitb.ac.in", role=UserRole.HOD,
            institution_id=iitb.id, department_id=me.id,
            designation=Designation.PROFESSOR)
        me.hod_id = hod_me.id

        hod_ee = await upsert_user(W2["hod_ee"],
            employee_id="IITB-H03", name="HOD-EE",
            email="hod.ee@iitb.ac.in", role=UserRole.HOD,
            institution_id=iitb.id, department_id=ee.id,
            designation=Designation.PROFESSOR)
        ee.hod_id = hod_ee.id

        print("\n[IITB Faculty — CS]")
        fi1 = await upsert_user(W2["fi1"],
            employee_id="IITB-F01", name="Dr. Arjun Mehta",
            email="arjun.mehta@iitb.ac.in", role=UserRole.FACULTY,
            institution_id=iitb.id, department_id=cs.id,
            designation=Designation.PROFESSOR)
        fi2 = await upsert_user(W2["fi2"],
            employee_id="IITB-F02", name="Dr. Kavya Reddy",
            email="kavya.reddy@iitb.ac.in", role=UserRole.FACULTY,
            institution_id=iitb.id, department_id=cs.id,
            designation=Designation.ASSOCIATE_PROFESSOR)
        fi3 = await upsert_user(W2["fi3"],
            employee_id="IITB-F03", name="Dr. Siddharth Joshi",
            email="siddharth.joshi@iitb.ac.in", role=UserRole.FACULTY,
            institution_id=iitb.id, department_id=cs.id,
            designation=Designation.ASSISTANT_PROFESSOR)

        print("\n[IITB Faculty — ME]")
        fi4 = await upsert_user(W2["fi4"],
            employee_id="IITB-F04", name="Dr. Rohan Kulkarni",
            email="rohan.kulkarni@iitb.ac.in", role=UserRole.FACULTY,
            institution_id=iitb.id, department_id=me.id,
            designation=Designation.PROFESSOR)
        fi5 = await upsert_user(W2["fi5"],
            employee_id="IITB-F05", name="Dr. Neha Sharma",
            email="neha.sharma@iitb.ac.in", role=UserRole.FACULTY,
            institution_id=iitb.id, department_id=me.id,
            designation=Designation.ASSOCIATE_PROFESSOR)

        print("\n[IITB Faculty — EE]")
        fi6 = await upsert_user(W2["fi6"],
            employee_id="IITB-F06", name="Dr. Vijay Bhat",
            email="vijay.bhat@iitb.ac.in", role=UserRole.FACULTY,
            institution_id=iitb.id, department_id=ee.id,
            designation=Designation.PROFESSOR)
        fi7 = await upsert_user(W2["fi7"],
            employee_id="IITB-F07", name="Dr. Pooja Iyer",
            email="pooja.iyer@iitb.ac.in", role=UserRole.FACULTY,
            institution_id=iitb.id, department_id=ee.id,
            designation=Designation.ASSISTANT_PROFESSOR)

        await session.commit()
        for obj in [hod_cs, hod_me, hod_ee, fi1, fi2, fi3, fi4, fi5, fi6, fi7]:
            await session.refresh(obj)

        # ── IITB Contributions ─────────────────────────────────────────────────
        print("\n[IITB Contributions]")
        iitb_contribs = [
            # Dr. Arjun Mehta
            dict(ipfs_hash="QmIITBArjun001TransformerCodeGen000000000000000",
                 metadata_hash="0xIITBMeta001A00000000000000000000000000000001",
                 faculty=fi1, category=ContributionCategory.REFEREED_JOURNAL,
                 title="Transformer-Based Code Generation for Low-Resource Programming Languages",
                 abstract=("We present CodeFormer, a transformer architecture fine-tuned on "
                           "multilingual code corpora for low-resource languages including Julia, "
                           "Rust, and Kotlin. Our model achieves 34% improvement in CodeBLEU over "
                           "GPT-4 baselines on unseen benchmarks, enabling automated code synthesis "
                           "for resource-constrained development environments with novel cross-lingual "
                           "transfer learning techniques."),
                 journal_name="ACM Transactions on Software Engineering",
                 doi="10.1145/IITB.2024.001",
                 publication_date=now - timedelta(days=75),
                 co_authors="Dr. K. Reddy, Dr. S. Patil",
                 status=ContributionStatus.VALIDATED,
                 ai_quality_score=85.0, novelty_percentage=78.0, base_credits=25.0,
                 reviewer=hod_cs,
                 review_notes="Outstanding work. Strong experimental results. Approved.",
                 review_time=now - timedelta(days=55),
                 submission_time=now - timedelta(days=70),
                 blockchain_id=2001,
                 blockchain_tx_hash="0xIITBTx001A0000000000000000000000000000001"),
            dict(ipfs_hash="QmIITBArjun002AttentionMechanisms0000000000000",
                 metadata_hash="0xIITBMeta002A00000000000000000000000000000002",
                 faculty=fi1, category=ContributionCategory.NATIONAL_CONFERENCE,
                 title="Comparative Analysis of Attention Mechanisms in Large Language Models",
                 abstract=("A systematic benchmark comparing self-attention, sparse attention, "
                           "linear attention, and flash-attention variants across six NLP tasks. "
                           "We show flash-attention achieves 3.2x inference speedup with only "
                           "0.4% accuracy degradation on GLUE benchmarks, making it the preferred "
                           "choice for production NLP deployments on constrained hardware."),
                 journal_name="Proc. AAAI India 2024",
                 doi=None,
                 publication_date=now - timedelta(days=20),
                 co_authors=None,
                 status=ContributionStatus.UNDER_REVIEW,
                 ai_quality_score=73.0, novelty_percentage=64.0, base_credits=10.0,
                 reviewer=hod_cs, review_notes=None, review_time=None,
                 submission_time=now - timedelta(days=14),
                 blockchain_id=2002,
                 blockchain_tx_hash="0xIITBTx002A0000000000000000000000000000002"),
            # Dr. Kavya Reddy
            dict(ipfs_hash="QmIITBKavya001FederatedLearningIoT00000000000",
                 metadata_hash="0xIITBMeta001B00000000000000000000000000000003",
                 faculty=fi2, category=ContributionCategory.RESEARCH_PROJECT,
                 title="Federated Learning Framework for Privacy-Preserving IoT Analytics",
                 abstract=("This research proposes FedIoT, a novel federated learning framework "
                           "that enables collaborative model training across IoT edge devices without "
                           "centralizing raw data. We introduce a differential privacy mechanism "
                           "with adaptive noise calibration that preserves 94% model accuracy while "
                           "providing epsilon=1.0 privacy guarantee across 500 heterogeneous devices."),
                 doi=None,
                 publication_date=now - timedelta(days=130),
                 co_authors="Dr. A. Mehta",
                 status=ContributionStatus.VALIDATED,
                 ai_quality_score=79.0, novelty_percentage=70.0, base_credits=20.0,
                 reviewer=hod_cs,
                 review_notes="Novel privacy framework with strong empirical validation.",
                 review_time=now - timedelta(days=100),
                 submission_time=now - timedelta(days=125),
                 blockchain_id=2003,
                 blockchain_tx_hash="0xIITBTx003B0000000000000000000000000000003"),
            dict(ipfs_hash="QmIITBKavya002GraphNNDrugDiscovery000000000000",
                 metadata_hash="0xIITBMeta002B00000000000000000000000000000004",
                 faculty=fi2, category=ContributionCategory.BOOK_CHAPTER,
                 title="Graph Neural Networks in Drug Discovery: Applications and Challenges",
                 abstract=("A comprehensive book chapter reviewing the application of graph neural "
                           "networks (GNNs) to molecular property prediction, drug-target interaction "
                           "modelling, and de novo drug design. Covers architectures including GCN, "
                           "GAT, and MPNN with case studies on COVID-19 antiviral candidate screening."),
                 isbn="978-1-234-56789-0",
                 publication_date=None,
                 co_authors=None,
                 status=ContributionStatus.PENDING,
                 ai_quality_score=0.0, novelty_percentage=0.0, base_credits=5.0,
                 reviewer=None, review_notes=None, review_time=None,
                 submission_time=now - timedelta(days=4),
                 blockchain_id=None, blockchain_tx_hash=None),
            # Dr. Siddharth Joshi
            dict(ipfs_hash="QmIITBSidh001ContainerResourceAlloc00000000000",
                 metadata_hash="0xIITBMeta001C00000000000000000000000000000005",
                 faculty=fi3, category=ContributionCategory.PATENT_FILED,
                 title="System and Method for Adaptive Resource Allocation in Containerized Microservices",
                 abstract=("A patented system for real-time adaptive CPU and memory allocation "
                           "in Kubernetes-managed microservice clusters using reinforcement learning. "
                           "The invention continuously monitors service latency SLOs and dynamically "
                           "re-partitions resources, achieving 28% reduction in over-provisioning "
                           "while maintaining 99.9% SLO compliance in production workloads."),
                 publication_date=None, co_authors="Dr. K. Reddy",
                 status=ContributionStatus.PENDING,
                 ai_quality_score=0.0, novelty_percentage=0.0, base_credits=15.0,
                 reviewer=None, review_notes=None, review_time=None,
                 submission_time=now - timedelta(days=2),
                 blockchain_id=None, blockchain_tx_hash=None),
            dict(ipfs_hash="QmIITBSidh002NoSQLSurvey000000000000000000000",
                 metadata_hash="0xIITBMeta002C00000000000000000000000000000006",
                 faculty=fi3, category=ContributionCategory.REFEREED_JOURNAL,
                 title="A Survey on NoSQL Database Query Optimization Techniques",
                 abstract=("A review of query optimization strategies in document, key-value, "
                           "columnar, and graph NoSQL databases, covering indexing, caching, "
                           "and query rewriting approaches used by MongoDB, Cassandra, and Neo4j."),
                 issn="1111-2222",
                 doi="10.1109/IITB.2024.002",
                 publication_date=now - timedelta(days=210),
                 co_authors=None,
                 status=ContributionStatus.REJECTED,
                 ai_quality_score=42.0, novelty_percentage=28.0, base_credits=25.0,
                 reviewer=hod_cs,
                 review_notes="Lacks original contribution; reads as a literature survey with no new methodology.",
                 review_time=now - timedelta(days=190),
                 submission_time=now - timedelta(days=205),
                 blockchain_id=2004,
                 blockchain_tx_hash="0xIITBTx004C0000000000000000000000000000004"),
            # Dr. Rohan Kulkarni
            dict(ipfs_hash="QmIITBRohan001CFDAdvancedBook0000000000000000",
                 metadata_hash="0xIITBMeta001D00000000000000000000000000000007",
                 faculty=fi4, category=ContributionCategory.INTERNATIONAL_BOOK,
                 title="Computational Fluid Dynamics: Advanced Topics in Turbulence Modelling",
                 abstract=("A graduate-level textbook covering advanced CFD methodologies including "
                           "Large Eddy Simulation, Detached Eddy Simulation, and hybrid RANS-LES "
                           "approaches for turbulent flow prediction. The book includes novel "
                           "benchmark cases derived from the authors' original wind-tunnel experiments "
                           "and validated OpenFOAM simulation pipelines."),
                 isbn="978-0-444-12345-6",
                 publication_date=now - timedelta(days=160),
                 co_authors="Prof. T. Nair",
                 status=ContributionStatus.VALIDATED,
                 ai_quality_score=76.0, novelty_percentage=65.0, base_credits=30.0,
                 reviewer=hod_me,
                 review_notes="Rigorous textbook with original benchmark contributions. Approved.",
                 review_time=now - timedelta(days=130),
                 submission_time=now - timedelta(days=155),
                 blockchain_id=2005,
                 blockchain_tx_hash="0xIITBTx005D0000000000000000000000000000005"),
            dict(ipfs_hash="QmIITBRohan002PredictiveMaintenanceTurbine000000",
                 metadata_hash="0xIITBMeta002D00000000000000000000000000000008",
                 faculty=fi4, category=ContributionCategory.RESEARCH_PROJECT,
                 title="AI-Driven Predictive Maintenance Framework for Industrial Gas Turbines",
                 abstract=("This project develops an end-to-end predictive maintenance system "
                           "for industrial gas turbines using multi-variate LSTM networks trained "
                           "on vibration, temperature, and pressure sensor streams. The system "
                           "detects bearing failures 72 hours in advance with 96% precision, "
                           "deployed and validated at two power generation facilities."),
                 doi=None,
                 publication_date=now - timedelta(days=18),
                 co_authors="Dr. N. Sharma, Mr. P. Desai",
                 status=ContributionStatus.UNDER_REVIEW,
                 ai_quality_score=81.0, novelty_percentage=74.0, base_credits=20.0,
                 reviewer=hod_me, review_notes=None, review_time=None,
                 submission_time=now - timedelta(days=12),
                 blockchain_id=2006,
                 blockchain_tx_hash="0xIITBTx006D0000000000000000000000000000006"),
            # Dr. Neha Sharma
            dict(ipfs_hash="QmIITBNeha001TopologyOptimization0000000000000",
                 metadata_hash="0xIITBMeta001E00000000000000000000000000000009",
                 faculty=fi5, category=ContributionCategory.NATIONAL_CONFERENCE,
                 title="Topology Optimization of Additively Manufactured Lattice Structures",
                 abstract=("This work proposes a SIMP-based topology optimization approach tailored "
                           "for FDM-printed polymer lattice structures accounting for anisotropic "
                           "build-direction material properties. Printed specimens show 18% higher "
                           "strength-to-weight ratio compared to isotropic-assumption-based designs."),
                 journal_name="Proc. AIMTDR 2024",
                 publication_date=None, co_authors=None,
                 status=ContributionStatus.PENDING,
                 ai_quality_score=0.0, novelty_percentage=0.0, base_credits=10.0,
                 reviewer=None, review_notes=None, review_time=None,
                 submission_time=now - timedelta(days=6),
                 blockchain_id=None, blockchain_tx_hash=None),
            dict(ipfs_hash="QmIITBNeha002MLMaterialsScience00000000000000",
                 metadata_hash="0xIITBMeta002E0000000000000000000000000000000A",
                 faculty=fi5, category=ContributionCategory.REFEREED_JOURNAL,
                 title="Machine Learning Applications in High-Entropy Alloy Property Prediction",
                 abstract=("We apply gradient-boosted decision trees and neural network ensembles "
                           "to predict hardness, yield strength, and fracture toughness of novel "
                           "high-entropy alloys from compositional descriptors. Training on 4,200 "
                           "literature samples, our model achieves R²=0.94 on held-out test sets, "
                           "accelerating alloy screening by 300x compared to DFT simulations."),
                 journal_name="Acta Materialia",
                 doi="10.1016/j.actamat.2024.003",
                 publication_date=now - timedelta(days=95),
                 co_authors="Dr. R. Kulkarni",
                 status=ContributionStatus.VALIDATED,
                 ai_quality_score=72.0, novelty_percentage=63.0, base_credits=25.0,
                 reviewer=hod_me,
                 review_notes="Strong methodology. Approved.",
                 review_time=now - timedelta(days=70),
                 submission_time=now - timedelta(days=90),
                 blockchain_id=2007,
                 blockchain_tx_hash="0xIITBTx007E0000000000000000000000000000007"),
            # Dr. Vijay Bhat
            dict(ipfs_hash="QmIITBVijay001GaNPowerConverterEV000000000000",
                 metadata_hash="0xIITBMeta001F0000000000000000000000000000000B",
                 faculty=fi6, category=ContributionCategory.REFEREED_JOURNAL,
                 title="High-Efficiency GaN-Based Bidirectional Converter for EV Fast Charging",
                 abstract=("This paper presents a novel GaN-based bidirectional DC-DC converter "
                           "topology for 150 kW EV fast-charging stations. A new switching modulation "
                           "scheme reduces switching losses by 31% achieving 98.4% peak efficiency. "
                           "Hardware prototype validated on a 60 kW test bench with full V2G capability "
                           "and integrated active thermal management."),
                 journal_name="IEEE Transactions on Power Electronics",
                 doi="10.1109/TPEL.2024.004",
                 publication_date=now - timedelta(days=50),
                 co_authors="Dr. P. Iyer",
                 status=ContributionStatus.VALIDATED,
                 ai_quality_score=83.0, novelty_percentage=76.0, base_credits=25.0,
                 reviewer=hod_ee,
                 review_notes="Excellent power electronics contribution with real hardware validation.",
                 review_time=now - timedelta(days=30),
                 submission_time=now - timedelta(days=45),
                 blockchain_id=2008,
                 blockchain_tx_hash="0xIITBTx008F0000000000000000000000000000008"),
            dict(ipfs_hash="QmIITBVijay002SmartGridRLFlagged000000000000",
                 metadata_hash="0xIITBMeta002F0000000000000000000000000000000C",
                 faculty=fi6, category=ContributionCategory.RESEARCH_PROJECT,
                 title="Smart Grid Demand Response Optimization Using Deep Reinforcement Learning",
                 abstract=("A novel deep Q-network agent trained to schedule deferrable loads "
                           "and coordinate distributed energy resources in a smart grid demand "
                           "response framework. Simulations on IEEE 33-bus test system show "
                           "19% peak load reduction while maintaining voltage stability constraints."),
                 doi=None,
                 publication_date=now - timedelta(days=35),
                 co_authors=None,
                 status=ContributionStatus.FLAGGED,
                 ai_quality_score=60.0, novelty_percentage=52.0, base_credits=20.0,
                 reviewer=hod_ee,
                 review_notes="Flagged: abstract similarity with an existing submission.",
                 review_time=now - timedelta(days=22),
                 is_flagged=True,
                 flag_reason="Abstract overlap > 82% with external publication",
                 fraud_score=0.84,
                 fraud_reasons=json.dumps(["abstract_similarity_high", "possible_self_plagiarism"]),
                 submission_time=now - timedelta(days=30),
                 blockchain_id=2009,
                 blockchain_tx_hash="0xIITBTx009F0000000000000000000000000000009"),
            # Dr. Pooja Iyer
            dict(ipfs_hash="QmIITBPooja001RenewableEnergyChapter000000000",
                 metadata_hash="0xIITBMeta001G000000000000000000000000000000D",
                 faculty=fi7, category=ContributionCategory.BOOK_CHAPTER,
                 title="Renewable Energy Integration Challenges in Modern Power Grids",
                 abstract=("A book chapter examining technical and regulatory challenges of "
                           "integrating high penetrations of solar and wind energy into legacy "
                           "transmission grids, covering frequency regulation, inertia emulation, "
                           "and grid-forming inverter control strategies."),
                 isbn="978-3-540-12345-7",
                 publication_date=None, co_authors="Dr. V. Bhat",
                 status=ContributionStatus.PENDING,
                 ai_quality_score=0.0, novelty_percentage=0.0, base_credits=5.0,
                 reviewer=None, review_notes=None, review_time=None,
                 submission_time=now - timedelta(days=3),
                 blockchain_id=None, blockchain_tx_hash=None),
            dict(ipfs_hash="QmIITBPooja002AdaptiveVoltagePatent000000000",
                 metadata_hash="0xIITBMeta002G000000000000000000000000000000E",
                 faculty=fi7, category=ContributionCategory.PATENT_FILED,
                 title="Method for Adaptive Voltage Regulation in Islanded Distributed Microgrids",
                 abstract=("A patented method for real-time voltage regulation in islanded microgrids "
                           "using a distributed consensus algorithm among smart inverters. Each "
                           "inverter exchanges only local measurements with neighbours, achieving "
                           "global voltage regulation within 50 ms without a central controller, "
                           "validated on a 12-bus hardware-in-the-loop microgrid testbed."),
                 publication_date=None, co_authors=None,
                 status=ContributionStatus.UNDER_REVIEW,
                 ai_quality_score=76.0, novelty_percentage=68.0, base_credits=15.0,
                 reviewer=hod_ee, review_notes=None, review_time=None,
                 submission_time=now - timedelta(days=8),
                 blockchain_id=2010,
                 blockchain_tx_hash="0xIITBTx010G000000000000000000000000000000A"),
        ]

        iitb_credits = {}
        for spec in iitb_contribs:
            if await contrib_exists(spec["ipfs_hash"]):
                print(f"  → skip: {spec['title'][:50]}…")
                continue
            base = spec["base_credits"]
            q = spec.get("ai_quality_score", 0.0)
            n = spec.get("novelty_percentage", 0.0)
            final = _credits(base, q, n) if spec["status"] == ContributionStatus.VALIDATED else 0.0
            fac: User = spec["faculty"]
            rev: User | None = spec.get("reviewer")
            c = Contribution(
                ipfs_hash=spec["ipfs_hash"], metadata_hash=spec["metadata_hash"],
                faculty_id=fac.id, faculty_address=fac.wallet_address,
                category=spec["category"], title=spec["title"], abstract=spec["abstract"],
                file_name=f"iitb_{fac.employee_id}_{spec['category'].value}.pdf",
                file_size=280_000,
                journal_name=spec.get("journal_name"), isbn=spec.get("isbn"),
                issn=spec.get("issn"), doi=spec.get("doi"),
                publication_date=spec.get("publication_date"),
                co_authors=spec.get("co_authors"),
                status=spec["status"], ai_quality_score=q, novelty_percentage=n,
                base_credits=base, final_credits=final,
                calculated_credits=_credits(base, q, n) if q > 0 else base,
                evaluation_details=_eval_details(q, n, spec["title"]) if q > 0 else None,
                reviewer_id=rev.id if rev else None,
                review_notes=spec.get("review_notes"), review_time=spec.get("review_time"),
                is_flagged=spec.get("is_flagged", False),
                flag_reason=spec.get("flag_reason"), fraud_score=spec.get("fraud_score", 0.0),
                fraud_reasons=spec.get("fraud_reasons"),
                submission_time=spec.get("submission_time", now),
                blockchain_id=spec.get("blockchain_id"),
                blockchain_tx_hash=spec.get("blockchain_tx_hash"),
                created_at=spec.get("submission_time", now),
            )
            session.add(c)
            if spec["status"] == ContributionStatus.VALIDATED:
                iitb_credits[fac.id] = iitb_credits.get(fac.id, 0.0) + final
            print(f"  ✓ {spec['status'].value:12s}  {spec['title'][:52]}…")

        await session.flush()

        # ════════════════════════════════════════════════════════════════════════
        # INSTITUTION 3 — RV College of Engineering
        # ════════════════════════════════════════════════════════════════════════
        print("\n[RV College of Engineering]")
        rvce = await upsert_inst("RVCE", "RV College of Engineering", W3["admin"])

        print("\n[RVCE Departments]")
        it    = await upsert_dept(rvce.id, "IT",    "Information Technology")
        civil = await upsert_dept(rvce.id, "CIVIL", "Civil Engineering")
        await upsert_dept(rvce.id, "CHEM", "Chemical Engineering")

        print("\n[RVCE Institute Admin]")
        rvce_ia = await upsert_user(W3["admin"],
            employee_id="RVCE-IA01", name="RVCE Institute Admin",
            email="iadmin@rvce.edu.in", role=UserRole.INSTITUTE_ADMIN,
            institution_id=rvce.id, designation=Designation.PROFESSOR)
        rvce.admin_address = rvce_ia.wallet_address

        print("\n[RVCE HoDs]")
        hod_it = await upsert_user(W3["hod_it"],
            employee_id="RVCE-H01", name="HOD-IT",
            email="hod.it@rvce.edu.in", role=UserRole.HOD,
            institution_id=rvce.id, department_id=it.id,
            designation=Designation.PROFESSOR)
        it.hod_id = hod_it.id

        hod_civil = await upsert_user(W3["hod_civil"],
            employee_id="RVCE-H02", name="HOD-CIVIL",
            email="hod.civil@rvce.edu.in", role=UserRole.HOD,
            institution_id=rvce.id, department_id=civil.id,
            designation=Designation.PROFESSOR)
        civil.hod_id = hod_civil.id

        print("\n[RVCE Faculty — IT]")
        fr1 = await upsert_user(W3["fr1"],
            employee_id="RVCE-F01", name="Dr. Kiran Nair",
            email="kiran.nair@rvce.edu.in", role=UserRole.FACULTY,
            institution_id=rvce.id, department_id=it.id,
            designation=Designation.PROFESSOR)
        fr2 = await upsert_user(W3["fr2"],
            employee_id="RVCE-F02", name="Dr. Meena Pillai",
            email="meena.pillai@rvce.edu.in", role=UserRole.FACULTY,
            institution_id=rvce.id, department_id=it.id,
            designation=Designation.ASSOCIATE_PROFESSOR)
        fr3 = await upsert_user(W3["fr3"],
            employee_id="RVCE-F03", name="Dr. Arun Shetty",
            email="arun.shetty@rvce.edu.in", role=UserRole.FACULTY,
            institution_id=rvce.id, department_id=it.id,
            designation=Designation.ASSISTANT_PROFESSOR)

        print("\n[RVCE Faculty — Civil]")
        fr4 = await upsert_user(W3["fr4"],
            employee_id="RVCE-F04", name="Dr. Sunita Rao",
            email="sunita.rao@rvce.edu.in", role=UserRole.FACULTY,
            institution_id=rvce.id, department_id=civil.id,
            designation=Designation.PROFESSOR)
        fr5 = await upsert_user(W3["fr5"],
            employee_id="RVCE-F05", name="Dr. Deepak Hegde",
            email="deepak.hegde@rvce.edu.in", role=UserRole.FACULTY,
            institution_id=rvce.id, department_id=civil.id,
            designation=Designation.ASSOCIATE_PROFESSOR)

        await session.commit()
        for obj in [hod_it, hod_civil, fr1, fr2, fr3, fr4, fr5]:
            await session.refresh(obj)

        # ── RVCE Contributions ─────────────────────────────────────────────────
        print("\n[RVCE Contributions]")
        rvce_contribs = [
            # Dr. Kiran Nair
            dict(ipfs_hash="QmRVCEKiran001CybersecurityICS0000000000000000",
                 metadata_hash="0xRVCEMeta001A00000000000000000000000000000001",
                 faculty=fr1, category=ContributionCategory.REFEREED_JOURNAL,
                 title="Cybersecurity Framework for Industrial Control Systems in Critical Infrastructure",
                 abstract=("We propose SecureICS, a layered cybersecurity framework for SCADA and "
                           "DCS-based industrial control systems compliant with IEC 62443. The "
                           "framework integrates anomaly-based intrusion detection using one-class "
                           "SVM trained on normal PLC traffic, achieving 97.3% detection rate with "
                           "only 0.6% false positives on the SWaT benchmark dataset."),
                 journal_name="Computers & Security",
                 doi="10.1016/j.cose.2024.005",
                 publication_date=now - timedelta(days=60),
                 co_authors="Dr. A. Shetty",
                 status=ContributionStatus.VALIDATED,
                 ai_quality_score=80.0, novelty_percentage=73.0, base_credits=25.0,
                 reviewer=hod_it,
                 review_notes="Practical security contribution with strong benchmarks. Approved.",
                 review_time=now - timedelta(days=40),
                 submission_time=now - timedelta(days=55),
                 blockchain_id=3001,
                 blockchain_tx_hash="0xRVCETx001A0000000000000000000000000000001"),
            dict(ipfs_hash="QmRVCEKiran002ZeroTrustCloud000000000000000000",
                 metadata_hash="0xRVCEMeta002A00000000000000000000000000000002",
                 faculty=fr1, category=ContributionCategory.NATIONAL_CONFERENCE,
                 title="Zero-Trust Architecture Implementation in Hybrid Enterprise Cloud Environments",
                 abstract=("A practical implementation guide and evaluation of zero-trust network "
                           "architecture for hybrid on-premise and cloud enterprises, covering "
                           "micro-segmentation, identity-aware proxies, and continuous verification. "
                           "Case study on a 1,200-user deployment demonstrates 61% reduction in "
                           "lateral-movement attack surface compared to perimeter-based model."),
                 journal_name="Proc. ICCNS 2024",
                 publication_date=None, co_authors=None,
                 status=ContributionStatus.PENDING,
                 ai_quality_score=0.0, novelty_percentage=0.0, base_credits=10.0,
                 reviewer=None, review_notes=None, review_time=None,
                 submission_time=now - timedelta(days=5),
                 blockchain_id=None, blockchain_tx_hash=None),
            # Dr. Meena Pillai
            dict(ipfs_hash="QmRVCEMeena001MultiModalSentiment000000000000",
                 metadata_hash="0xRVCEMeta001B00000000000000000000000000000003",
                 faculty=fr2, category=ContributionCategory.RESEARCH_PROJECT,
                 title="Multi-Modal Cross-Lingual Sentiment Analysis Using Contrastive Transformers",
                 abstract=("This project develops a multi-modal transformer that jointly encodes "
                           "text, audio, and facial expression features for sentiment analysis across "
                           "10 languages without parallel corpora. A novel cross-lingual contrastive "
                           "objective aligns sentiment representations across modalities and languages, "
                           "outperforming mBERT by 8.4% on MulSen-21 benchmark."),
                 doi=None,
                 publication_date=now - timedelta(days=22),
                 co_authors="Dr. K. Nair, Ms. R. Thomas",
                 status=ContributionStatus.UNDER_REVIEW,
                 ai_quality_score=75.0, novelty_percentage=67.0, base_credits=20.0,
                 reviewer=hod_it, review_notes=None, review_time=None,
                 submission_time=now - timedelta(days=16),
                 blockchain_id=3002,
                 blockchain_tx_hash="0xRVCETx002B0000000000000000000000000000002"),
            dict(ipfs_hash="QmRVCEMeena002CybersecurityTextbook000000000",
                 metadata_hash="0xRVCEMeta002B00000000000000000000000000000004",
                 faculty=fr2, category=ContributionCategory.NATIONAL_BOOK,
                 title="Introduction to Cybersecurity for Engineering Students",
                 abstract=("An undergraduate textbook introducing fundamental cybersecurity concepts "
                           "including cryptography, network security, and ethical hacking basics, "
                           "designed for non-CS engineering students with no prior security background."),
                 isbn="978-81-234-5678-9",
                 publication_date=now - timedelta(days=240),
                 co_authors=None,
                 status=ContributionStatus.REJECTED,
                 ai_quality_score=48.0, novelty_percentage=32.0, base_credits=20.0,
                 reviewer=hod_it,
                 review_notes="Content is introductory with no research contribution. Recommend submission to educational publishers only.",
                 review_time=now - timedelta(days=215),
                 submission_time=now - timedelta(days=235),
                 blockchain_id=3003,
                 blockchain_tx_hash="0xRVCETx003B0000000000000000000000000000003"),
            # Dr. Arun Shetty
            dict(ipfs_hash="QmRVCEArun001IntrusionDetectionPatent000000000",
                 metadata_hash="0xRVCEMeta001C00000000000000000000000000000005",
                 faculty=fr3, category=ContributionCategory.PATENT_FILED,
                 title="Apparatus for Real-Time Network Intrusion Detection Using Federated ML",
                 abstract=("A patented apparatus for distributed real-time network intrusion detection "
                           "where individual network nodes collaboratively train anomaly detection models "
                           "using federated learning without sharing raw packet data. The system detects "
                           "zero-day exploits within 200 ms of first occurrence, with a validated prototype "
                           "deployed across 50 enterprise nodes in a live testbed."),
                 publication_date=None, co_authors="Dr. K. Nair",
                 status=ContributionStatus.PENDING,
                 ai_quality_score=0.0, novelty_percentage=0.0, base_credits=15.0,
                 reviewer=None, review_notes=None, review_time=None,
                 submission_time=now - timedelta(days=1),
                 blockchain_id=None, blockchain_tx_hash=None),
            dict(ipfs_hash="QmRVCEArun002LightweightCryptoIoT0000000000000",
                 metadata_hash="0xRVCEMeta002C00000000000000000000000000000006",
                 faculty=fr3, category=ContributionCategory.NATIONAL_CONFERENCE,
                 title="ASCON-Based Lightweight Cryptography Implementation for 8-bit Microcontrollers",
                 abstract=("This paper presents an optimized assembly-level implementation of the "
                           "NIST-selected ASCON lightweight authenticated encryption scheme on "
                           "AVR ATmega328 microcontrollers. Achieving 11 cycles/byte throughput "
                           "at 16 MHz with 512 bytes RAM footprint, our implementation enables "
                           "standards-compliant IoT security on the lowest-cost hardware tier."),
                 journal_name="Proc. NCC 2025",
                 doi=None,
                 publication_date=now - timedelta(days=110),
                 co_authors=None,
                 status=ContributionStatus.VALIDATED,
                 ai_quality_score=67.0, novelty_percentage=57.0, base_credits=10.0,
                 reviewer=hod_it,
                 review_notes="Technically sound, well-benchmarked implementation. Approved.",
                 review_time=now - timedelta(days=88),
                 submission_time=now - timedelta(days=105),
                 blockchain_id=3004,
                 blockchain_tx_hash="0xRVCETx004C0000000000000000000000000000004"),
            # Dr. Sunita Rao
            dict(ipfs_hash="QmRVCESunita001StructuralHealthMonitoring000000",
                 metadata_hash="0xRVCEMeta001D00000000000000000000000000000007",
                 faculty=fr4, category=ContributionCategory.RESEARCH_PROJECT,
                 title="AI-Based Structural Health Monitoring of Reinforced Concrete Bridges",
                 abstract=("This research develops a sensor-fusion SHM system for reinforced concrete "
                           "bridges combining accelerometers, strain gauges, and acoustic emission "
                           "sensors with a multi-task deep learning model for simultaneous damage "
                           "localisation and severity classification. Validated on a 1:10 scale "
                           "bridge specimen, detecting crack initiation with 0.5 mm resolution."),
                 doi=None,
                 publication_date=now - timedelta(days=140),
                 co_authors="Prof. R. Hegde, Dr. D. Hegde",
                 status=ContributionStatus.VALIDATED,
                 ai_quality_score=77.0, novelty_percentage=67.0, base_credits=20.0,
                 reviewer=hod_civil,
                 review_notes="Strong applied research with experimental validation. Approved.",
                 review_time=now - timedelta(days=110),
                 submission_time=now - timedelta(days=135),
                 blockchain_id=3005,
                 blockchain_tx_hash="0xRVCETx005D0000000000000000000000000000005"),
            dict(ipfs_hash="QmRVCESunita002SustainableMaterialsReview00000",
                 metadata_hash="0xRVCEMeta002D00000000000000000000000000000008",
                 faculty=fr4, category=ContributionCategory.REFEREED_JOURNAL,
                 title="Sustainable Construction Materials: Life-Cycle Assessment and Carbon Footprint",
                 abstract=("A systematic literature review and meta-analysis of life-cycle assessments "
                           "for alternative cementitious materials including fly ash, GGBS, silica fume, "
                           "and alkali-activated binders. Meta-regression across 87 LCA studies quantifies "
                           "CO₂ savings of 40–70% versus OPC concrete, with recommendations for Indian "
                           "construction sector adoption policy."),
                 issn="0950-0618",
                 doi=None,
                 publication_date=now - timedelta(days=25),
                 co_authors=None,
                 status=ContributionStatus.UNDER_REVIEW,
                 ai_quality_score=74.0, novelty_percentage=65.0, base_credits=25.0,
                 reviewer=hod_civil, review_notes=None, review_time=None,
                 submission_time=now - timedelta(days=18),
                 blockchain_id=3006,
                 blockchain_tx_hash="0xRVCETx006D0000000000000000000000000000006"),
            # Dr. Deepak Hegde
            dict(ipfs_hash="QmRVCEDeepak001GISFloodRisk0000000000000000000",
                 metadata_hash="0xRVCEMeta001E00000000000000000000000000000009",
                 faculty=fr5, category=ContributionCategory.NATIONAL_CONFERENCE,
                 title="GIS-Based Urban Flood Risk Assessment Using SWMM and Remote Sensing Data",
                 abstract=("A GIS-integrated storm-water management model (SWMM) calibrated with "
                           "Sentinel-2 LULC and LiDAR DEM data to map 100-year flood inundation "
                           "extents in Bengaluru's Bellandur watershed. The model identifies 12 "
                           "high-risk zones covering 4,800 ha and proposes low-impact development "
                           "interventions reducing peak runoff by 23%."),
                 journal_name="Proc. HYDRO 2024",
                 publication_date=None, co_authors="Dr. S. Rao",
                 status=ContributionStatus.PENDING,
                 ai_quality_score=0.0, novelty_percentage=0.0, base_credits=10.0,
                 reviewer=None, review_notes=None, review_time=None,
                 submission_time=now - timedelta(days=7),
                 blockchain_id=None, blockchain_tx_hash=None),
            dict(ipfs_hash="QmRVCEDeepak002SmartInfraBookChapter000000000",
                 metadata_hash="0xRVCEMeta002E0000000000000000000000000000000A",
                 faculty=fr5, category=ContributionCategory.BOOK_CHAPTER,
                 title="Smart Infrastructure and IoT Integration for Next-Generation Civil Systems",
                 abstract=("This book chapter reviews IoT sensor networks, digital twins, and edge "
                           "computing integration in smart civil infrastructure including bridges, "
                           "tunnels, and water distribution networks. Covers communication protocols, "
                           "data management pipelines, and decision-support system architectures "
                           "used in three international smart city deployments."),
                 isbn="978-0-12-819123-4",
                 publication_date=now - timedelta(days=105),
                 co_authors="Dr. S. Rao",
                 status=ContributionStatus.VALIDATED,
                 ai_quality_score=70.0, novelty_percentage=60.0, base_credits=5.0,
                 reviewer=hod_civil,
                 review_notes="Well-written chapter with practical relevance. Approved.",
                 review_time=now - timedelta(days=80),
                 submission_time=now - timedelta(days=100),
                 blockchain_id=3007,
                 blockchain_tx_hash="0xRVCETx007E0000000000000000000000000000007"),
        ]

        rvce_credits = {}
        for spec in rvce_contribs:
            if await contrib_exists(spec["ipfs_hash"]):
                print(f"  → skip: {spec['title'][:50]}…")
                continue
            base = spec["base_credits"]
            q = spec.get("ai_quality_score", 0.0)
            n = spec.get("novelty_percentage", 0.0)
            final = _credits(base, q, n) if spec["status"] == ContributionStatus.VALIDATED else 0.0
            fac: User = spec["faculty"]
            rev: User | None = spec.get("reviewer")
            c = Contribution(
                ipfs_hash=spec["ipfs_hash"], metadata_hash=spec["metadata_hash"],
                faculty_id=fac.id, faculty_address=fac.wallet_address,
                category=spec["category"], title=spec["title"], abstract=spec["abstract"],
                file_name=f"rvce_{fac.employee_id}_{spec['category'].value}.pdf",
                file_size=220_000,
                journal_name=spec.get("journal_name"), isbn=spec.get("isbn"),
                issn=spec.get("issn"), doi=spec.get("doi"),
                publication_date=spec.get("publication_date"),
                co_authors=spec.get("co_authors"),
                status=spec["status"], ai_quality_score=q, novelty_percentage=n,
                base_credits=base, final_credits=final,
                calculated_credits=_credits(base, q, n) if q > 0 else base,
                evaluation_details=_eval_details(q, n, spec["title"]) if q > 0 else None,
                reviewer_id=rev.id if rev else None,
                review_notes=spec.get("review_notes"), review_time=spec.get("review_time"),
                is_flagged=spec.get("is_flagged", False),
                flag_reason=spec.get("flag_reason"), fraud_score=spec.get("fraud_score", 0.0),
                fraud_reasons=spec.get("fraud_reasons"),
                submission_time=spec.get("submission_time", now),
                blockchain_id=spec.get("blockchain_id"),
                blockchain_tx_hash=spec.get("blockchain_tx_hash"),
                created_at=spec.get("submission_time", now),
            )
            session.add(c)
            if spec["status"] == ContributionStatus.VALIDATED:
                rvce_credits[fac.id] = rvce_credits.get(fac.id, 0.0) + final
            print(f"  ✓ {spec['status'].value:12s}  {spec['title'][:52]}…")

        await session.flush()

        # ── Update total_credits ───────────────────────────────────────────────
        print("\n[Updating total_credits]")
        for uid, credits in {**iitb_credits, **rvce_credits}.items():
            u = (await session.execute(select(User).where(User.id == uid))).scalar_one()
            u.total_credits = round(credits, 2)
            print(f"  ✓ {u.name}: {u.total_credits} credits")

        await session.commit()
        print("\n✅  Extra seed complete.\n")


# ── Wallets for RIT ───────────────────────────────────────────────────────────
W4 = {
    "admin":       "0xAa00000000000000000000000000000000000030",
    "hod_cse":     "0xBb00000000000000000000000000000000000031",
    "hod_ece":     "0xCc00000000000000000000000000000000000032",
    "hod_mech":    "0xDd00000000000000000000000000000000000033",
    "hod_civil":   "0xEe00000000000000000000000000000000000034",
    "hod_aiml":    "0xFF00000000000000000000000000000000000035",
    "r1":          "0xaa00000000000000000000000000000000000036",
    "r2":          "0xBB00000000000000000000000000000000000037",
    "r3":          "0xcc00000000000000000000000000000000000038",
    "r4":          "0xDD00000000000000000000000000000000000039",
    "r5":          "0xee00000000000000000000000000000000000040",
    "r6":          "0xAA00000000000000000000000000000000000041",
    "r7":          "0xbb00000000000000000000000000000000000042",
    "r8":          "0xCC00000000000000000000000000000000000043",
    "r9":          "0xdd00000000000000000000000000000000000044",
    "r10":         "0xEE00000000000000000000000000000000000045",
    "r11":         "0xFF00000000000000000000000000000000000046",
    "r12":         "0xaa00000000000000000000000000000000000047",
    "r13":         "0xBB00000000000000000000000000000000000048",
}


async def seed_rit():
    """Seed RIT — Ramaiah Institute of Technology — with 5 depts, 5 HODs, 13 faculty, 37 contributions."""

    async with AsyncSessionLocal() as session:

        async def upsert_inst(code, name, admin_wallet):
            obj = (await session.execute(
                select(Institution).where(Institution.code == code)
            )).scalar_one_or_none()
            if obj is None:
                obj = Institution(code=code, name=name, admin_address=admin_wallet,
                                  is_active=True, created_at=datetime.utcnow())
                session.add(obj)
                await session.flush()
                print(f"  ✓ {code} – {name}")
            else:
                print(f"  → exists: {code}")
            return obj

        async def upsert_dept(inst_id, code, name):
            obj = (await session.execute(
                select(Department).where(Department.institution_id == inst_id,
                                         Department.code == code)
            )).scalar_one_or_none()
            if obj is None:
                obj = Department(institution_id=inst_id, code=code, name=name,
                                 is_active=True, created_at=datetime.utcnow())
                session.add(obj)
                await session.flush()
                print(f"    dept ✓ {code}")
            else:
                print(f"    dept → exists {code}")
            return obj

        async def upsert_user(wallet, **kw):
            obj = (await session.execute(
                select(User).where(User.wallet_address == wallet)
            )).scalar_one_or_none()
            if obj is None:
                obj = User(wallet_address=wallet, **kw,
                           is_active=True, total_credits=0.0,
                           created_at=datetime.utcnow())
                session.add(obj)
                await session.flush()
                print(f"    user ✓ {kw['name']}")
            else:
                print(f"    user → exists {kw['name']}")
            return obj

        async def contrib_exists(ipfs_hash):
            return (await session.execute(
                select(Contribution).where(Contribution.ipfs_hash == ipfs_hash)
            )).scalar_one_or_none() is not None

        now = datetime.utcnow()

        # ── Institution ────────────────────────────────────────────────────────
        print("\n[RIT – Ramaiah Institute of Technology]")
        rit = await upsert_inst("RIT", "Ramaiah Institute of Technology", W4["admin"])

        # ── Departments ────────────────────────────────────────────────────────
        print("\n  [Departments]")
        d_cse  = await upsert_dept(rit.id, "CSE",  "Computer Science & Engineering")
        d_ece  = await upsert_dept(rit.id, "ECE",  "Electronics & Communication Engineering")
        d_mech = await upsert_dept(rit.id, "MECH", "Mechanical Engineering")
        d_civ  = await upsert_dept(rit.id, "CIVIL","Civil Engineering")
        d_aiml = await upsert_dept(rit.id, "AIML", "Artificial Intelligence & Machine Learning")

        # ── Institute Admin ────────────────────────────────────────────────────
        print("\n  [Institute Admin]")
        rit_ia = await upsert_user(W4["admin"],
            employee_id="RIT-IA01", name="RIT Institute Admin",
            email="iadmin@rit.edu.in", role=UserRole.INSTITUTE_ADMIN,
            institution_id=rit.id, designation=Designation.PROFESSOR)
        rit.admin_address = rit_ia.wallet_address

        # ── HoDs ──────────────────────────────────────────────────────────────
        print("\n  [HoDs]")
        hod_cse  = await upsert_user(W4["hod_cse"],
            employee_id="RIT-H01", name="HOD-CSE",
            email="hod.cse@rit.edu.in", role=UserRole.HOD,
            institution_id=rit.id, department_id=d_cse.id,
            designation=Designation.PROFESSOR)
        d_cse.hod_id = hod_cse.id

        hod_ece  = await upsert_user(W4["hod_ece"],
            employee_id="RIT-H02", name="HOD-ECE",
            email="hod.ece@rit.edu.in", role=UserRole.HOD,
            institution_id=rit.id, department_id=d_ece.id,
            designation=Designation.PROFESSOR)
        d_ece.hod_id = hod_ece.id

        hod_mech = await upsert_user(W4["hod_mech"],
            employee_id="RIT-H03", name="HOD-MECH",
            email="hod.mech@rit.edu.in", role=UserRole.HOD,
            institution_id=rit.id, department_id=d_mech.id,
            designation=Designation.PROFESSOR)
        d_mech.hod_id = hod_mech.id

        hod_civ  = await upsert_user(W4["hod_civil"],
            employee_id="RIT-H04", name="HOD-CIVIL",
            email="hod.civil@rit.edu.in", role=UserRole.HOD,
            institution_id=rit.id, department_id=d_civ.id,
            designation=Designation.PROFESSOR)
        d_civ.hod_id = hod_civ.id

        hod_aiml = await upsert_user(W4["hod_aiml"],
            employee_id="RIT-H05", name="HOD-AIML",
            email="hod.aiml@rit.edu.in", role=UserRole.HOD,
            institution_id=rit.id, department_id=d_aiml.id,
            designation=Designation.PROFESSOR)
        d_aiml.hod_id = hod_aiml.id

        # ── Faculty ────────────────────────────────────────────────────────────
        print("\n  [Faculty — CSE]")
        r1 = await upsert_user(W4["r1"], employee_id="RIT-F01",
            name="Dr. Rahul Agarwal", email="rahul.agarwal@rit.edu.in",
            role=UserRole.FACULTY, institution_id=rit.id, department_id=d_cse.id,
            designation=Designation.PROFESSOR)
        r2 = await upsert_user(W4["r2"], employee_id="RIT-F02",
            name="Dr. Priyanka Joshi", email="priyanka.joshi@rit.edu.in",
            role=UserRole.FACULTY, institution_id=rit.id, department_id=d_cse.id,
            designation=Designation.ASSOCIATE_PROFESSOR)
        r3 = await upsert_user(W4["r3"], employee_id="RIT-F03",
            name="Dr. Naveen Kumar", email="naveen.kumar@rit.edu.in",
            role=UserRole.FACULTY, institution_id=rit.id, department_id=d_cse.id,
            designation=Designation.ASSISTANT_PROFESSOR)

        print("\n  [Faculty — ECE]")
        r4 = await upsert_user(W4["r4"], employee_id="RIT-F04",
            name="Dr. Suresh Patil", email="suresh.patil@rit.edu.in",
            role=UserRole.FACULTY, institution_id=rit.id, department_id=d_ece.id,
            designation=Designation.PROFESSOR)
        r5 = await upsert_user(W4["r5"], employee_id="RIT-F05",
            name="Dr. Kavitha Menon", email="kavitha.menon@rit.edu.in",
            role=UserRole.FACULTY, institution_id=rit.id, department_id=d_ece.id,
            designation=Designation.ASSOCIATE_PROFESSOR)

        print("\n  [Faculty — MECH]")
        r6 = await upsert_user(W4["r6"], employee_id="RIT-F06",
            name="Dr. Aditya Bhatt", email="aditya.bhatt@rit.edu.in",
            role=UserRole.FACULTY, institution_id=rit.id, department_id=d_mech.id,
            designation=Designation.PROFESSOR)
        r7 = await upsert_user(W4["r7"], employee_id="RIT-F07",
            name="Dr. Smita Deshmukh", email="smita.deshmukh@rit.edu.in",
            role=UserRole.FACULTY, institution_id=rit.id, department_id=d_mech.id,
            designation=Designation.ASSOCIATE_PROFESSOR)
        r8 = await upsert_user(W4["r8"], employee_id="RIT-F08",
            name="Dr. Rajan Tiwari", email="rajan.tiwari@rit.edu.in",
            role=UserRole.FACULTY, institution_id=rit.id, department_id=d_mech.id,
            designation=Designation.ASSISTANT_PROFESSOR)

        print("\n  [Faculty — CIVIL]")
        r9  = await upsert_user(W4["r9"], employee_id="RIT-F09",
            name="Dr. Geeta Sharma", email="geeta.sharma@rit.edu.in",
            role=UserRole.FACULTY, institution_id=rit.id, department_id=d_civ.id,
            designation=Designation.PROFESSOR)
        r10 = await upsert_user(W4["r10"], employee_id="RIT-F10",
            name="Dr. Manohar Rao", email="manohar.rao@rit.edu.in",
            role=UserRole.FACULTY, institution_id=rit.id, department_id=d_civ.id,
            designation=Designation.ASSOCIATE_PROFESSOR)

        print("\n  [Faculty — AI/ML]")
        r11 = await upsert_user(W4["r11"], employee_id="RIT-F11",
            name="Dr. Lakshmi Narayanan", email="lakshmi.n@rit.edu.in",
            role=UserRole.FACULTY, institution_id=rit.id, department_id=d_aiml.id,
            designation=Designation.PROFESSOR)
        r12 = await upsert_user(W4["r12"], employee_id="RIT-F12",
            name="Dr. Dinesh Choudhary", email="dinesh.choudhary@rit.edu.in",
            role=UserRole.FACULTY, institution_id=rit.id, department_id=d_aiml.id,
            designation=Designation.ASSOCIATE_PROFESSOR)
        r13 = await upsert_user(W4["r13"], employee_id="RIT-F13",
            name="Dr. Pallavi Srivastava", email="pallavi.s@rit.edu.in",
            role=UserRole.FACULTY, institution_id=rit.id, department_id=d_aiml.id,
            designation=Designation.ASSISTANT_PROFESSOR)

        await session.commit()
        for obj in [hod_cse, hod_ece, hod_mech, hod_civ, hod_aiml,
                    r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13]:
            await session.refresh(obj)

        # ── Contributions ──────────────────────────────────────────────────────
        print("\n  [Contributions]")

        def _c(ipfs, meta, fac, cat, title, abstract, status, q, n, base,
               reviewer=None, review_notes=None, review_time=None,
               days_ago=30, journal=None, isbn=None, issn=None, doi=None,
               co_authors=None, publication_date=None,
               blockchain_id=None, blockchain_tx=None,
               is_flagged=False, flag_reason=None, fraud_score=0.0, fraud_reasons=None):
            return dict(
                ipfs_hash=ipfs, metadata_hash=meta,
                faculty=fac, category=cat, title=title, abstract=abstract,
                status=status, ai_quality_score=q, novelty_percentage=n, base_credits=base,
                reviewer=reviewer, review_notes=review_notes, review_time=review_time,
                submission_time=now - timedelta(days=days_ago),
                journal_name=journal, isbn=isbn, issn=issn, doi=doi,
                co_authors=co_authors, publication_date=publication_date,
                blockchain_id=blockchain_id, blockchain_tx_hash=blockchain_tx,
                is_flagged=is_flagged, flag_reason=flag_reason,
                fraud_score=fraud_score, fraud_reasons=fraud_reasons,
            )

        V = ContributionStatus.VALIDATED
        UR = ContributionStatus.UNDER_REVIEW
        P = ContributionStatus.PENDING
        RJ = ContributionStatus.REJECTED
        FL = ContributionStatus.FLAGGED

        specs = [
            # ── Dr. Rahul Agarwal (CSE) ────────────────────────────────────────
            _c("QmRITRahul001SecureMPCML00000000000000000000000",
               "0xRITMeta001r1000000000000000000000000000000001",
               r1, ContributionCategory.REFEREED_JOURNAL,
               "Secure Multi-Party Computation for Privacy-Preserving Federated Learning",
               ("We present CryptoFed, a novel secure multi-party computation protocol enabling "
                "federated learning across mutually distrusting organizations. Using additive "
                "secret sharing and garbled circuits, CryptoFed eliminates gradient leakage "
                "while achieving only 1.8x communication overhead versus plaintext federated "
                "learning, validated on CIFAR-100 and clinical chest X-ray datasets."),
               V, 84.0, 76.0, 25.0,
               reviewer=hod_cse, review_notes="Pioneering privacy-preserving ML work. Approved.",
               review_time=now - timedelta(days=55),
               days_ago=70, journal="IEEE Transactions on Information Forensics & Security",
               doi="10.1109/TIFS.2024.RIT001",
               publication_date=now - timedelta(days=65),
               co_authors="Dr. P. Joshi",
               blockchain_id=4001, blockchain_tx="0xRITTx001r1000000000000000000000000000001"),
            _c("QmRITRahul002ServerlessEdgeVideo0000000000000000",
               "0xRITMeta002r1000000000000000000000000000000002",
               r1, ContributionCategory.RESEARCH_PROJECT,
               "Serverless Edge Computing Framework for Real-Time Video Analytics",
               ("This project builds FrameFlow, a serverless computing framework deploying "
                "object-detection inference functions at 5G MEC nodes. Dynamic function "
                "chaining with ML-based workload prediction reduces end-to-end latency by 54% "
                "and cold-start overhead by 78% compared to vanilla Kubernetes on a 20-node "
                "edge cluster serving HD video streams."),
               V, 77.0, 68.0, 20.0,
               reviewer=hod_cse, review_notes="Strong systems contribution with real deployment.",
               review_time=now - timedelta(days=100),
               days_ago=120, doi=None,
               publication_date=now - timedelta(days=110),
               co_authors="Dr. N. Kumar",
               blockchain_id=4002, blockchain_tx="0xRITTx002r1000000000000000000000000000002"),
            _c("QmRITRahul003NASPatentPending0000000000000000000",
               "0xRITMeta003r1000000000000000000000000000000003",
               r1, ContributionCategory.PATENT_FILED,
               "Method for Neural Architecture Search in Resource-Constrained Embedded Environments",
               ("A patented method combining differentiable NAS with hardware-aware latency "
                "predictors to automatically discover neural architectures meeting user-defined "
                "latency and memory budgets on microcontrollers. The search finds Pareto-optimal "
                "architectures 120x faster than random search on ARM Cortex-M4 targets."),
               P, 0.0, 0.0, 15.0, days_ago=4,
               blockchain_id=None, blockchain_tx=None),

            # ── Dr. Priyanka Joshi (CSE) ───────────────────────────────────────
            _c("QmRITPriyanka001XAIClinical000000000000000000000",
               "0xRITMeta001r2000000000000000000000000000000004",
               r2, ContributionCategory.REFEREED_JOURNAL,
               "Explainable AI in Clinical Decision Support: A SHAP-Based Framework",
               ("We develop an explainable clinical decision support system for ICU mortality "
                "prediction using gradient-boosted ensembles with SHAP-based post-hoc "
                "explanations. A user study with 42 clinicians confirms our explanations "
                "improve trust calibration and reduce over-reliance errors by 29%."),
               UR, 76.0, 68.0, 25.0,
               reviewer=hod_cse, review_notes=None, review_time=None,
               days_ago=15, journal="Journal of Biomedical Informatics",
               doi="10.1016/j.jbi.2024.RIT002",
               publication_date=now - timedelta(days=10),
               co_authors="Dr. R. Agarwal",
               blockchain_id=4003, blockchain_tx="0xRITTx003r2000000000000000000000000000003"),
            _c("QmRITPriyanka002GenModelsDataAug000000000000000",
               "0xRITMeta002r2000000000000000000000000000000005",
               r2, ContributionCategory.NATIONAL_CONFERENCE,
               "Comparative Study of Generative Models for Imbalanced Medical Image Augmentation",
               ("A systematic comparison of VAE, GAN, and Diffusion model-based augmentation "
                "strategies for minority-class medical image synthesis on three imbalanced "
                "datasets. Diffusion-based augmentation yields the highest downstream classifier "
                "F1 (+11.4%) but 6x slower generation; we provide practical selection guidelines."),
               V, 68.0, 59.0, 10.0,
               reviewer=hod_cse, review_notes="Useful benchmark paper. Approved.",
               review_time=now - timedelta(days=80),
               days_ago=95, journal="Proc. ISBI 2024",
               publication_date=now - timedelta(days=85),
               blockchain_id=4004, blockchain_tx="0xRITTx004r2000000000000000000000000000004"),
            _c("QmRITPriyanka003AITestingChapter0000000000000000",
               "0xRITMeta003r2000000000000000000000000000000006",
               r2, ContributionCategory.BOOK_CHAPTER,
               "Modern Approaches to AI-Assisted Software Testing: Mutation Testing and Beyond",
               ("A book chapter covering AI-driven software testing methodologies including "
                "LLM-based test case generation, neural mutation testing, and property-based "
                "fuzzing. Includes comparative case studies from industry deployments."),
               P, 0.0, 0.0, 5.0, days_ago=3,
               isbn="978-1-000-12345-6"),

            # ── Dr. Naveen Kumar (CSE) ─────────────────────────────────────────
            _c("QmRITNaveen001IoTFirmwareVulnPatent000000000000",
               "0xRITMeta001r3000000000000000000000000000000007",
               r3, ContributionCategory.PATENT_FILED,
               "System for Automated Firmware Vulnerability Detection in IoT Devices Using Static Analysis",
               ("A patented system that performs scalable binary static analysis of IoT "
                "firmware images to detect common vulnerability patterns including buffer "
                "overflows, format string bugs, and hardcoded credentials. Evaluated on 12,000 "
                "real-world firmware images from CVE database, achieving 94.1% detection rate."),
               P, 0.0, 0.0, 15.0, days_ago=2),
            _c("QmRITNaveen002DBIndexReview000000000000000000000",
               "0xRITMeta002r3000000000000000000000000000000008",
               r3, ContributionCategory.REFEREED_JOURNAL,
               "Survey of Query Optimization and Indexing Strategies in Relational Databases",
               ("A broad survey of classical and modern indexing structures and query "
                "optimization heuristics in RDBMS, covering B-tree variants, hash indexes, "
                "and cost-based query planners without novel contributions."),
               RJ, 40.0, 25.0, 25.0,
               reviewer=hod_cse,
               review_notes="Survey lacks original contributions and is below research threshold for this venue.",
               review_time=now - timedelta(days=160),
               days_ago=175, issn="0001-0782",
               doi="10.1145/RIT.2024.003",
               publication_date=now - timedelta(days=170),
               blockchain_id=4005, blockchain_tx="0xRITTx005r3000000000000000000000000000005"),
            _c("QmRITNaveen003DockerMLConf00000000000000000000000",
               "0xRITMeta003r3000000000000000000000000000000009",
               r3, ContributionCategory.NATIONAL_CONFERENCE,
               "ML-Driven Prediction of Container Startup Latency for Serverless Scheduling",
               ("We train an XGBoost model to predict Docker container cold-start latency "
                "from image metadata, allowing Kubernetes schedulers to pre-warm containers "
                "proactively. On a 100-node cluster benchmark, pre-warming reduces P99 "
                "cold-start from 4.2 s to 0.6 s with 93% prediction accuracy."),
               UR, 71.0, 63.0, 10.0,
               reviewer=hod_cse, review_notes=None, review_time=None,
               days_ago=12, journal="Proc. IEEE CloudCom 2024",
               blockchain_id=4006, blockchain_tx="0xRITTx006r3000000000000000000000000000006"),

            # ── Dr. Suresh Patil (ECE) ─────────────────────────────────────────
            _c("QmRITSuresh001PVMPPTFuzzyLogic000000000000000000",
               "0xRITMeta001r4000000000000000000000000000000010",
               r4, ContributionCategory.REFEREED_JOURNAL,
               "Adaptive Fuzzy-Logic MPPT Control for Photovoltaic Systems Under Partial Shading",
               ("We propose an adaptive fuzzy-logic maximum power point tracking (MPPT) "
                "controller for PV systems handling partial shading conditions. The controller "
                "dynamically adjusts membership functions based on irradiance gradient, "
                "improving energy harvest by 18.3% over P&O under 40% shading on a 5 kW "
                "prototype and validated against IEC 61724 standards."),
               V, 79.0, 70.0, 25.0,
               reviewer=hod_ece,
               review_notes="Novel adaptive MPPT contribution with solid hardware validation. Approved.",
               review_time=now - timedelta(days=45),
               days_ago=60, journal="Solar Energy",
               doi="10.1016/j.solener.2024.RIT004",
               publication_date=now - timedelta(days=55),
               co_authors="Dr. K. Menon",
               blockchain_id=4007, blockchain_tx="0xRITTx007r4000000000000000000000000000007"),
            _c("QmRITSuresh002DPD5GNR000000000000000000000000000",
               "0xRITMeta002r4000000000000000000000000000000011",
               r4, ContributionCategory.RESEARCH_PROJECT,
               "Behavioural Modelling and Digital Predistortion for 5G NR Power Amplifiers",
               ("This project develops Volterra-series digital predistortion (DPD) linearisation "
                "for GaN Doherty power amplifiers targeting 5G NR sub-6 GHz bands. An "
                "FPGA-implemented adaptive DPD reduces EVM from 8.2% to 1.1% and improves ACLR "
                "by 22 dB at 43 dBm output power on a 100 MHz 5G NR test signal."),
               UR, 78.0, 69.0, 20.0,
               reviewer=hod_ece, review_notes=None, review_time=None,
               days_ago=18, co_authors="Dr. S. Patil",
               blockchain_id=4008, blockchain_tx="0xRITTx008r4000000000000000000000000000008"),
            _c("QmRITSuresh003InternLecture6G00000000000000000000",
               "0xRITMeta003r4000000000000000000000000000000012",
               r4, ContributionCategory.INTERNATIONAL_LECTURE,
               "Invited Lecture: RF Front-End Challenges and Opportunities in 6G Communication",
               ("An invited lecture delivered at IEEE APMC 2024 (Kuala Lumpur) covering "
                "sub-THz transceiver design challenges, reconfigurable intelligent surfaces, "
                "and integrated sensing-and-communication (ISAC) for 6G, with discussion of "
                "open research problems in RF hardware and signal processing."),
               P, 0.0, 0.0, 7.0, days_ago=6),

            # ── Dr. Kavitha Menon (ECE) ────────────────────────────────────────
            _c("QmRITKavitha001FPGAAES256IoT000000000000000000000",
               "0xRITMeta001r5000000000000000000000000000000013",
               r5, ContributionCategory.NATIONAL_CONFERENCE,
               "High-Throughput FPGA Implementation of AES-256-GCM for Resource-Constrained IoT",
               ("We present an optimised FPGA implementation of AES-256-GCM authenticated "
                "encryption on Xilinx Artix-7, achieving 4.2 Gbps throughput at 1,847 LUTs "
                "and 512 FFs — 2.3x area-efficient versus prior art — enabling TLS 1.3 in "
                "constrained IoT gateways meeting IEC 62351 security requirements."),
               V, 72.0, 62.0, 10.0,
               reviewer=hod_ece,
               review_notes="Well-optimised hardware security work. Approved.",
               review_time=now - timedelta(days=90),
               days_ago=105, journal="Proc. VLSI Design 2024",
               publication_date=now - timedelta(days=95),
               blockchain_id=4009, blockchain_tx="0xRITTx009r5000000000000000000000000000009"),
            _c("QmRITKavitha002PMUPlacementJournal0000000000000000",
               "0xRITMeta002r5000000000000000000000000000000014",
               r5, ContributionCategory.REFEREED_JOURNAL,
               "Optimal PMU Placement for Complete Observability of Smart Transmission Networks",
               ("A mixed-integer linear programming (MILP) formulation for minimum PMU "
                "placement ensuring full smart grid observability under single-channel failure, "
                "incorporating zero-injection bus constraints. Solved on IEEE 118-bus test "
                "system, reducing PMU count by 14% versus heuristic methods."),
               P, 0.0, 0.0, 25.0, days_ago=5,
               issn="0885-8950"),
            _c("QmRITKavitha003ECGArrhythmiaFlagged0000000000000",
               "0xRITMeta003r5000000000000000000000000000000015",
               r5, ContributionCategory.RESEARCH_PROJECT,
               "AI-Assisted 12-Lead ECG Arrhythmia Detection Using Deep Residual Networks",
               ("This project applies ResNet-34 to 12-lead ECG classification across "
                "15 arrhythmia types on the PhysioNet 2020 dataset, achieving 91.4% macro-F1. "
                "A novel attention mechanism highlights clinically relevant waveform segments "
                "for cardiologist review, with deployment on a clinical-grade ECG device."),
               FL, 58.0, 49.0, 20.0,
               reviewer=hod_ece,
               review_notes="Flagged: significant overlap with a published paper from another institution.",
               review_time=now - timedelta(days=28),
               days_ago=40,
               is_flagged=True,
               flag_reason="Abstract similarity 87% with external publication",
               fraud_score=0.87,
               fraud_reasons=json.dumps(["high_abstract_similarity", "possible_duplicate"]),
               blockchain_id=4010, blockchain_tx="0xRITTx010r5000000000000000000000000000010"),

            # ── Dr. Aditya Bhatt (MECH) ────────────────────────────────────────
            _c("QmRITAditya001AdvMfgIndustry4Book000000000000000",
               "0xRITMeta001r6000000000000000000000000000000016",
               r6, ContributionCategory.INTERNATIONAL_BOOK,
               "Advanced Manufacturing Processes: An Industry 4.0 Perspective",
               ("A comprehensive graduate textbook synthesising smart manufacturing, digital "
                "twins, additive manufacturing, and cyber-physical systems under the Industry "
                "4.0 paradigm. Includes original case studies from automotive and aerospace "
                "sectors co-developed with industry partners, with 18 novel benchmark problems."),
               V, 80.0, 71.0, 30.0,
               reviewer=hod_mech,
               review_notes="Authoritative industry 4.0 textbook with original industrial cases. Approved.",
               review_time=now - timedelta(days=130),
               days_ago=155, isbn="978-0-12-000001-1",
               publication_date=now - timedelta(days=145),
               co_authors="Prof. K. Ramesh",
               blockchain_id=4011, blockchain_tx="0xRITTx011r6000000000000000000000000000011"),
            _c("QmRITAditya002DigitalTwinQuality00000000000000000",
               "0xRITMeta002r6000000000000000000000000000000017",
               r6, ContributionCategory.REFEREED_JOURNAL,
               "Digital Twin-Based In-Process Quality Control in Automotive Body Panel Stamping",
               ("A real-time digital twin framework synchronises FEA simulation with strain "
                "gauge and vision sensor data during sheet metal stamping to predict springback "
                "and surface defects. Deployed on a production press line, it reduces scrap "
                "rate by 31% and rework time by 44% compared to statistical SPC methods."),
               UR, 81.0, 73.0, 25.0,
               reviewer=hod_mech, review_notes=None, review_time=None,
               days_ago=14, journal="CIRP Annals",
               doi="10.1016/j.cirp.2024.RIT005",
               blockchain_id=4012, blockchain_tx="0xRITTx012r6000000000000000000000000000012"),
            _c("QmRITAditya003HydrogenFuelCell000000000000000000",
               "0xRITMeta003r6000000000000000000000000000000018",
               r6, ContributionCategory.RESEARCH_PROJECT,
               "Hydrogen Fuel Cell-Battery Hybrid Powertrain for Commercial Vehicles",
               ("A research project developing an energy management strategy for a fuel-cell "
                "and lithium-ion battery hybrid powertrain in a 12-tonne truck. A dynamic "
                "programming-based supervisory controller reduces hydrogen consumption by 22% "
                "over rule-based control on real-world driving cycles."),
               P, 0.0, 0.0, 20.0, days_ago=7),

            # ── Dr. Smita Deshmukh (MECH) ──────────────────────────────────────
            _c("QmRITSmita001MultiObjAMOptimize000000000000000000",
               "0xRITMeta001r7000000000000000000000000000000019",
               r7, ContributionCategory.REFEREED_JOURNAL,
               "Multi-Objective Bayesian Optimization of FDM Process Parameters for Structural Parts",
               ("We apply multi-objective Bayesian optimization with Gaussian process surrogates "
                "to simultaneously maximize tensile strength and minimize surface roughness in "
                "FDM-printed PLA structural parts. The approach finds Pareto-front solutions "
                "in 40 experiments, reducing trial count by 70% versus full-factorial DOE."),
               V, 74.0, 64.0, 25.0,
               reviewer=hod_mech,
               review_notes="Novel optimization approach for AM. Approved.",
               review_time=now - timedelta(days=70),
               days_ago=85, journal="Journal of Manufacturing Science and Engineering",
               doi="10.1115/RIT.2024.006",
               publication_date=now - timedelta(days=78),
               co_authors="Dr. R. Tiwari",
               blockchain_id=4013, blockchain_tx="0xRITTx013r7000000000000000000000000000013"),
            _c("QmRITSmita002WasteHeatORCConf000000000000000000",
               "0xRITMeta002r7000000000000000000000000000000020",
               r7, ContributionCategory.NATIONAL_CONFERENCE,
               "Thermoeconomic Optimisation of Organic Rankine Cycles for Industrial Waste Heat",
               ("Thermoeconomic modelling of ORC systems recovering waste heat (80–200 °C) from "
                "cement kiln exhaust, comparing R245fa, R1233zd and ethanol working fluids. "
                "R1233zd ORC with regeneration achieves best net present value at 14.2% IRR "
                "over a 15-year plant horizon."),
               P, 0.0, 0.0, 10.0, days_ago=5,
               journal="Proc. NMD-ATM 2024"),
            _c("QmRITSmita003SustainableMfgChapter00000000000000",
               "0xRITMeta003r7000000000000000000000000000000021",
               r7, ContributionCategory.BOOK_CHAPTER,
               "Sustainable Manufacturing Technologies: Life-Cycle Thinking and Circular Economy",
               ("This chapter reviews LCA methodology, design for disassembly, remanufacturing "
                "strategies, and industrial symbiosis networks, contextualising circular economy "
                "principles for manufacturing engineers with four industry case studies."),
               UR, 70.0, 60.0, 5.0,
               reviewer=hod_mech, review_notes=None, review_time=None,
               days_ago=10, isbn="978-3-030-12345-6",
               blockchain_id=4014, blockchain_tx="0xRITTx014r7000000000000000000000000000014"),

            # ── Dr. Rajan Tiwari (MECH) ────────────────────────────────────────
            _c("QmRITRajan001CNCToolWearPatent0000000000000000000",
               "0xRITMeta001r8000000000000000000000000000000022",
               r8, ContributionCategory.PATENT_FILED,
               "Apparatus for Real-Time Tool Wear Monitoring in CNC Turning Using Acoustic Emission",
               ("A patented in-process tool wear monitoring system using acoustic emission "
                "sensors with an on-edge LSTM classifier to detect flank wear in real time "
                "during CNC turning without interrupting machining. Achieves tool-life "
                "prediction within ±8% error over 3,200 cutting trials."),
               P, 0.0, 0.0, 15.0, days_ago=3),
            _c("QmRITRajan002WindTurbineVibIoT000000000000000000",
               "0xRITMeta002r8000000000000000000000000000000023",
               r8, ContributionCategory.NATIONAL_CONFERENCE,
               "Vibration Signature Analysis of Wind Turbine Blades Using Low-Cost IoT Sensors",
               ("Accelerometer-based vibration monitoring deployed on 2 MW wind turbine blades "
                "detects leading-edge erosion and delamination via empirical mode decomposition "
                "and SVM classification. Field results across 8 turbines over 6 months show "
                "92% fault detection rate at 3x lower cost than commercial CMS systems."),
               V, 66.0, 56.0, 10.0,
               reviewer=hod_mech,
               review_notes="Practical and cost-effective SHM contribution. Approved.",
               review_time=now - timedelta(days=60),
               days_ago=75, journal="Proc. ICOVP 2024",
               publication_date=now - timedelta(days=70),
               blockchain_id=4015, blockchain_tx="0xRITTx015r8000000000000000000000000000015"),
            _c("QmRITRajan003EditorialWorkRejected0000000000000",
               "0xRITMeta003r8000000000000000000000000000000024",
               r8, ContributionCategory.EDITORIAL_WORK,
               "Guest Editor Activity for Journal of Mechanical Science (Special Issue)",
               ("Served as guest editor for a special issue on smart manufacturing, coordinating "
                "peer review for 14 submitted manuscripts, of which 6 were accepted after "
                "revision, over a 4-month editorial period."),
               RJ, 35.0, 20.0, 10.0,
               reviewer=hod_mech,
               review_notes="Does not meet the threshold for credit — editorial role without accompanying research output.",
               review_time=now - timedelta(days=140),
               days_ago=155,
               blockchain_id=4016, blockchain_tx="0xRITTx016r8000000000000000000000000000016"),

            # ── Dr. Geeta Sharma (CIVIL) ───────────────────────────────────────
            _c("QmRITGeeta001SmartWaterIoT000000000000000000000",
               "0xRITMeta001r9000000000000000000000000000000025",
               r9, ContributionCategory.RESEARCH_PROJECT,
               "Smart Water Distribution Network Monitoring and Leak Detection Using IoT and ML",
               ("This project deploys a WSN of 120 pressure and flow sensors across a "
                "2.4 km pilot water distribution network in a residential colony. A random-"
                "forest classifier detects pipe burst events within 90 seconds with 96.8% "
                "accuracy and localises leaks within a 50 m pipe segment using hydraulic "
                "inversion, reducing non-revenue water by 34%."),
               V, 75.0, 65.0, 20.0,
               reviewer=hod_civ,
               review_notes="Excellent applied project with field validation. Approved.",
               review_time=now - timedelta(days=95),
               days_ago=115, co_authors="Dr. M. Rao",
               publication_date=now - timedelta(days=105),
               blockchain_id=4017, blockchain_tx="0xRITTx017r9000000000000000000000000000017"),
            _c("QmRITGeeta002SeismicRCBuildings000000000000000000",
               "0xRITMeta002r9000000000000000000000000000000026",
               r9, ContributionCategory.REFEREED_JOURNAL,
               "Seismic Fragility Assessment of RC Frame Buildings with Soft-Story Irregularities",
               ("Incremental dynamic analysis of 6-storey RC frames with first-storey pilotis "
                "under 44 ground motion records characterises inter-storey drift fragility. "
                "Retrofit using energy-dissipating buckling-restrained braces at the soft storey "
                "reduces collapse probability from 38% to 7% at MCE shaking level."),
               UR, 76.0, 66.0, 25.0,
               reviewer=hod_civ, review_notes=None, review_time=None,
               days_ago=20, journal="Engineering Structures",
               doi="10.1016/j.engstruct.2024.RIT007",
               blockchain_id=4018, blockchain_tx="0xRITTx018r9000000000000000000000000000018"),
            _c("QmRITGeeta003UAVPavementConf000000000000000000000",
               "0xRITMeta003r9000000000000000000000000000000027",
               r9, ContributionCategory.NATIONAL_CONFERENCE,
               "UAV-Based Pavement Distress Detection Using YOLOv8 and Orthophotogrammetry",
               ("YOLOv8 trained on 8,400 annotated UAV images detects and classifies 6 pavement "
                "distress types with 89% mAP@0.5, enabling automated road condition surveys "
                "at 4.2 km/h inspection speed — 5x faster than manual walking inspections — "
                "validated on 11 km of urban roads in Bengaluru."),
               P, 0.0, 0.0, 10.0, days_ago=6,
               journal="Proc. IRC 2024"),

            # ── Dr. Manohar Rao (CIVIL) ────────────────────────────────────────
            _c("QmRITManohar001EIAGuideBook00000000000000000000",
               "0xRITMeta001r10000000000000000000000000000000028",
               r10, ContributionCategory.NATIONAL_BOOK,
               "Environmental Impact Assessment: A Practical Guide for Indian Projects",
               ("A practitioner's handbook covering EIA methodology, scoping, baseline data "
                "collection, impact prediction, and public consultation processes as per Indian "
                "EIA Notification 2006 and its 2020 amendments. Includes worked examples from "
                "highway, thermal power, and mining projects."),
               V, 69.0, 58.0, 20.0,
               reviewer=hod_civ,
               review_notes="Valuable practical reference for Indian EIA practice. Approved.",
               review_time=now - timedelta(days=110),
               days_ago=130, isbn="978-81-000-12345-0",
               publication_date=now - timedelta(days=120),
               blockchain_id=4019, blockchain_tx="0xRITTx019r10000000000000000000000000000019"),
            _c("QmRITManohar002GreenBuildingResearch000000000000",
               "0xRITMeta002r10000000000000000000000000000000029",
               r10, ContributionCategory.RESEARCH_PROJECT,
               "Green Building Rating Framework Calibration for Hot-Humid and Composite Indian Climates",
               ("This project recalibrates GRIHA and LEED credit weightings for hot-humid "
                "and composite climate zones using weighted principal component analysis on "
                "measured energy and thermal comfort data from 68 certified buildings, "
                "proposing climate-specific credit rebalancing to better reflect local priorities."),
               P, 0.0, 0.0, 20.0, days_ago=8, co_authors="Dr. G. Sharma"),
            _c("QmRITManohar003GroundwaterGISJournal000000000000",
               "0xRITMeta003r10000000000000000000000000000000030",
               r10, ContributionCategory.REFEREED_JOURNAL,
               "Spatiotemporal Groundwater Quality Analysis Using GIS, Remote Sensing and WQI",
               ("Integration of Sentinel-2 land-use data with 5-year groundwater quality "
                "monitoring across 94 wells in a peri-urban aquifer to compute water quality "
                "indices (WQI) and identify contamination hotspots. Random forest identifies "
                "agricultural runoff and septic leachate as primary contributors with 88% accuracy."),
               UR, 73.0, 63.0, 25.0,
               reviewer=hod_civ, review_notes=None, review_time=None,
               days_ago=17, journal="Journal of Hydrology",
               doi="10.1016/j.jhydrol.2024.RIT008",
               blockchain_id=4020, blockchain_tx="0xRITTx020r10000000000000000000000000000020"),

            # ── Dr. Lakshmi Narayanan (AI/ML) ──────────────────────────────────
            _c("QmRITLakshmi001SelfSupervisedMedImg000000000000",
               "0xRITMeta001r11000000000000000000000000000000031",
               r11, ContributionCategory.REFEREED_JOURNAL,
               "Self-Supervised Contrastive Learning for Medical Image Analysis Without Annotations",
               ("MedCLR, a novel contrastive pre-training framework for 3D medical images, "
                "learns anatomically meaningful representations without any labels using "
                "anatomy-preserving augmentations. Fine-tuned with 1% labelled data, MedCLR "
                "matches fully supervised baselines on BraTS and NIH-ChestX-ray14, enabling "
                "label-efficient clinical AI development."),
               V, 87.0, 80.0, 25.0,
               reviewer=hod_aiml,
               review_notes="Excellent self-supervised medical AI contribution. Top-tier work. Approved.",
               review_time=now - timedelta(days=40),
               days_ago=55, journal="Nature Machine Intelligence",
               doi="10.1038/s42256-2024-RIT009",
               publication_date=now - timedelta(days=48),
               co_authors="Dr. D. Choudhary",
               blockchain_id=4021, blockchain_tx="0xRITTx021r11000000000000000000000000000021"),
            _c("QmRITLakshmi002LLMIndianLangAdapt000000000000000",
               "0xRITMeta002r11000000000000000000000000000000032",
               r11, ContributionCategory.RESEARCH_PROJECT,
               "Instruction-Tuned LLM Adaptation for 12 Indian Regional Languages",
               ("This project develops IndicLLM-3B, a 3-billion parameter instruction-tuned "
                "language model covering Hindi, Tamil, Telugu, Kannada, and 8 other Indian "
                "languages. Using cross-lingual transfer and LoRA fine-tuning on 14M "
                "instruction pairs, IndicLLM-3B outperforms mT0-11B on IndicGLUE at 1/4 the "
                "parameter count, enabling deployment on consumer hardware."),
               V, 82.0, 74.0, 20.0,
               reviewer=hod_aiml,
               review_notes="Impactful multilingual NLP research for underserved languages. Approved.",
               review_time=now - timedelta(days=75),
               days_ago=90, co_authors="Dr. P. Srivastava",
               publication_date=now - timedelta(days=82),
               blockchain_id=4022, blockchain_tx="0xRITTx022r11000000000000000000000000000022"),
            _c("QmRITLakshmi003AEScoringPatentGranted00000000000",
               "0xRITMeta003r11000000000000000000000000000000033",
               r11, ContributionCategory.PATENT_GRANTED,
               "AI-Based Automated Essay Scoring System with Formative Feedback Generation",
               ("A granted patent for an NLP pipeline scoring student essays on coherence, "
                "argumentation, vocabulary, and grammar with a trait-specific BERT ensemble, "
                "and generating actionable formative feedback using a T5-based text generation "
                "model. Commercial deployment in two national assessment programmes."),
               UR, 83.0, 75.0, 30.0,
               reviewer=hod_aiml, review_notes=None, review_time=None,
               days_ago=22,
               blockchain_id=4023, blockchain_tx="0xRITTx023r11000000000000000000000000000023"),

            # ── Dr. Dinesh Choudhary (AI/ML) ───────────────────────────────────
            _c("QmRITDinesh001KnowledgeDistillNLP000000000000000",
               "0xRITMeta001r12000000000000000000000000000000034",
               r12, ContributionCategory.NATIONAL_CONFERENCE,
               "Progressive Knowledge Distillation for On-Device Transformer Inference",
               ("We present a progressive layer-by-layer distillation scheme transferring "
                "knowledge from a 110 M-parameter BERT teacher to a 6 M-parameter student "
                "while retaining 97.8% F1 on SQuAD 2.0. The student runs at 34 tokens/s on "
                "a Raspberry Pi 4 with 82 MB memory footprint — enabling offline NLP on IoT."),
               V, 70.0, 61.0, 10.0,
               reviewer=hod_aiml,
               review_notes="Practical on-device NLP contribution. Approved.",
               review_time=now - timedelta(days=85),
               days_ago=100, journal="Proc. ACL Findings 2024",
               publication_date=now - timedelta(days=92),
               co_authors="Dr. L. Narayanan",
               blockchain_id=4024, blockchain_tx="0xRITTx024r12000000000000000000000000000024"),
            _c("QmRITDinesh002CausalInferenceHealth000000000000",
               "0xRITMeta002r12000000000000000000000000000000035",
               r12, ContributionCategory.REFEREED_JOURNAL,
               "Causal Inference for Treatment Effect Estimation in Observational Healthcare Data",
               ("We apply doubly robust AIPW estimators with propensity score matching to "
                "estimate heterogeneous treatment effects of statin therapy on cardiovascular "
                "outcomes in a 280,000-patient EHR cohort. Causal forest identifies high-"
                "benefit subgroups and quantifies effect modification by diabetes and age."),
               P, 0.0, 0.0, 25.0, days_ago=9,
               journal="Journal of the American Medical Informatics Association"),
            _c("QmRITDinesh003MultiAgentSupplyChain0000000000000",
               "0xRITMeta003r12000000000000000000000000000000036",
               r12, ContributionCategory.RESEARCH_PROJECT,
               "Multi-Agent Deep Reinforcement Learning for Supply Chain Network Optimization",
               ("A multi-agent DDPG framework optimises joint inventory replenishment, "
                "routing, and pricing decisions across a 5-tier supply chain under stochastic "
                "demand. Trained in a discrete-event simulation calibrated with real retail "
                "data, the policy reduces total cost by 19% and stockout rate by 43% versus "
                "industry-standard (s,S) inventory policies."),
               UR, 76.0, 67.0, 20.0,
               reviewer=hod_aiml, review_notes=None, review_time=None,
               days_ago=16,
               blockchain_id=4025, blockchain_tx="0xRITTx025r12000000000000000000000000000025"),

            # ── Dr. Pallavi Srivastava (AI/ML) ─────────────────────────────────
            _c("QmRITPallavi001DeepfakeDetectPatent000000000000",
               "0xRITMeta001r13000000000000000000000000000000037",
               r13, ContributionCategory.PATENT_FILED,
               "Method for Real-Time Video Deepfake Detection Using Temporal Inconsistency Analysis",
               ("A patented deepfake detection pipeline identifying temporal inconsistencies "
                "in facial geometry and micro-expressions across video frames using a BiLSTM-"
                "Attention network. Achieves 97.2% AUC on FaceForensics++ and 94.8% on "
                "DFD at 25 fps on a GPU — suitable for real-time social media content moderation."),
               P, 0.0, 0.0, 15.0, days_ago=1),
            _c("QmRITPallavi002BiasMitigationHiring000000000000",
               "0xRITMeta002r13000000000000000000000000000000038",
               r13, ContributionCategory.NATIONAL_CONFERENCE,
               "Fairness-Aware Adversarial Debiasing for AI-Driven Hiring Algorithms",
               ("We apply adversarial debiasing to a resume screening classifier to enforce "
                "equal opportunity fairness across gender and ethnicity while maintaining "
                "78% predictive accuracy. A real-world audit on 12,000 anonymised CVs shows "
                "demographic parity gap reduces from 23% to 2.8% post-debiasing."),
               V, 68.0, 58.0, 10.0,
               reviewer=hod_aiml,
               review_notes="Timely AI fairness contribution with empirical evaluation. Approved.",
               review_time=now - timedelta(days=68),
               days_ago=82, journal="Proc. ECAI 2024",
               publication_date=now - timedelta(days=74),
               blockchain_id=4026, blockchain_tx="0xRITTx026r13000000000000000000000000000026"),
            _c("QmRITPallavi003TransferLowResourceFlagged0000000",
               "0xRITMeta003r13000000000000000000000000000000039",
               r13, ContributionCategory.REFEREED_JOURNAL,
               "Cross-Lingual Transfer Learning for Low-Resource South Asian Languages",
               ("An investigation of zero-shot and few-shot cross-lingual transfer from "
                "high-resource to low-resource South Asian languages using multilingual "
                "pre-trained models, with novel data augmentation using back-translation "
                "and vocabulary extension strategies."),
               FL, 54.0, 47.0, 25.0,
               reviewer=hod_aiml,
               review_notes="Flagged: high textual overlap with existing published work by same author group.",
               review_time=now - timedelta(days=35),
               days_ago=48,
               is_flagged=True,
               flag_reason="Overlap >80% with author's own prior paper — possible self-plagiarism",
               fraud_score=0.82,
               fraud_reasons=json.dumps(["self_plagiarism_detected", "abstract_overlap_high"]),
               blockchain_id=4027, blockchain_tx="0xRITTx027r13000000000000000000000000000027"),
        ]

        rit_credits = {}
        for spec in specs:
            if await contrib_exists(spec["ipfs_hash"]):
                print(f"    → skip: {spec['title'][:50]}…")
                continue
            base = spec["base_credits"]
            q    = spec.get("ai_quality_score", 0.0)
            n    = spec.get("novelty_percentage", 0.0)
            final = _credits(base, q, n) if spec["status"] == ContributionStatus.VALIDATED else 0.0
            fac: User = spec["faculty"]
            rev = spec.get("reviewer")
            c = Contribution(
                ipfs_hash=spec["ipfs_hash"], metadata_hash=spec["metadata_hash"],
                faculty_id=fac.id, faculty_address=fac.wallet_address,
                category=spec["category"], title=spec["title"], abstract=spec["abstract"],
                file_name=f"rit_{fac.employee_id}_{spec['category'].value}.pdf",
                file_size=240_000,
                journal_name=spec.get("journal_name"), isbn=spec.get("isbn"),
                issn=spec.get("issn"), doi=spec.get("doi"),
                publication_date=spec.get("publication_date"),
                co_authors=spec.get("co_authors"),
                status=spec["status"], ai_quality_score=q, novelty_percentage=n,
                base_credits=base, final_credits=final,
                calculated_credits=_credits(base, q, n) if q > 0 else base,
                evaluation_details=_eval_details(q, n, spec["title"]) if q > 0 else None,
                reviewer_id=rev.id if rev else None,
                review_notes=spec.get("review_notes"), review_time=spec.get("review_time"),
                is_flagged=spec.get("is_flagged", False),
                flag_reason=spec.get("flag_reason"), fraud_score=spec.get("fraud_score", 0.0),
                fraud_reasons=spec.get("fraud_reasons"),
                submission_time=spec.get("submission_time", now),
                blockchain_id=spec.get("blockchain_id"),
                blockchain_tx_hash=spec.get("blockchain_tx_hash"),
                created_at=spec.get("submission_time", now),
            )
            session.add(c)
            if spec["status"] == ContributionStatus.VALIDATED:
                rit_credits[fac.id] = rit_credits.get(fac.id, 0.0) + final
            print(f"    ✓ {spec['status'].value:12s}  {spec['title'][:50]}…")

        await session.flush()

        print("\n  [Updating total_credits]")
        for uid, credits in rit_credits.items():
            u = (await session.execute(select(User).where(User.id == uid))).scalar_one()
            u.total_credits = round(credits, 2)
            print(f"    ✓ {u.name}: {u.total_credits} credits")

        await session.commit()
        print("\n✅  RIT seed complete.\n")


if __name__ == "__main__":
    async def main():
        await seed()
        await seed_extra()
        await seed_rit()
    asyncio.run(main())
