"""
Seed FacultyProfile data (lectures, projects, courses) for all active faculty & HoD.
Run: venv/bin/python seed_profiles.py
"""
import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import AsyncSessionLocal
from app.models.database import User, FacultyProfile, UserRole
from sqlalchemy import select

# ─── Data Pools ──────────────────────────────────────────────────────────────

LECTURE_POOL = [
    {"subject": "Introduction to Machine Learning", "details": "Covered supervised & unsupervised learning, decision trees, SVMs, and neural networks. Delivered to 3rd year B.E. students. Included hands-on lab on scikit-learn."},
    {"subject": "Blockchain Technology & Decentralised Applications", "details": "Overview of distributed ledger, consensus mechanisms, smart contracts using Solidity on Ethereum. Audience: final-year CSE students."},
    {"subject": "Cloud Computing Architectures", "details": "Covered IaaS, PaaS, SaaS models, AWS and Azure services, containerisation with Docker and Kubernetes."},
    {"subject": "Cybersecurity & Ethical Hacking", "details": "Session on OWASP Top-10, penetration testing methodologies, CTF challenges. Delivered at national-level tech fest."},
    {"subject": "Natural Language Processing with Transformers", "details": "Deep dive into BERT, GPT architectures, attention mechanism, fine-tuning for downstream tasks."},
    {"subject": "Internet of Things: Protocols & Applications", "details": "MQTT, CoAP, edge computing, smart-city case studies. Lab on Raspberry Pi sensor integration."},
    {"subject": "Data Structures & Algorithm Design", "details": "Advanced graph algorithms, dynamic programming patterns, amortised analysis. Workshop at state-level college fest."},
    {"subject": "VLSI Design & Verification", "details": "RTL design using Verilog, functional verification with SystemVerilog, industry-standard EDA tools."},
    {"subject": "Digital Signal Processing", "details": "FIR/IIR filters, FFT applications, MATLAB simulations. Invited lecture series for ECE department."},
    {"subject": "Renewable Energy Systems", "details": "Solar PV modelling, wind-turbine aerodynamics, grid-integration challenges. Guest lecture at IEEE student chapter."},
    {"subject": "Agile Software Development & DevOps", "details": "Scrum, Kanban, CI/CD pipelines, infrastructure as code. Practical session with GitHub Actions demo."},
    {"subject": "Finite Element Analysis in Civil Structures", "details": "Structural modelling, mesh generation, stress analysis using ANSYS. Workshop for post-graduate students."},
    {"subject": "Deep Learning for Computer Vision", "details": "CNN architectures—ResNet, EfficientNet—transfer learning, object detection using YOLO."},
    {"subject": "Embedded Systems & Real-Time OS", "details": "FreeRTOS scheduling, bare-metal programming on STM32, CAN bus communication."},
    {"subject": "Operations Research & Optimisation", "details": "Linear programming, simplex method, metaheuristics—GA and PSO—applied to engineering problems."},
    {"subject": "Big Data Analytics with Spark", "details": "Hadoop ecosystem, Apache Spark RDDs, DataFrames, streaming analytics with Kafka."},
    {"subject": "Human-Computer Interaction Design", "details": "UX research methods, wireframing, usability testing, accessibility standards."},
    {"subject": "Advanced Database Systems", "details": "Query optimisation, distributed databases, NoSQL—MongoDB, Cassandra—CAP theorem."},
    {"subject": "Compiler Design Principles", "details": "Lexing, parsing, semantic analysis, intermediate code generation and optimisation."},
    {"subject": "Ethics in Artificial Intelligence", "details": "Bias, fairness, explainability, regulatory frameworks like EU AI Act. Panel discussion format."},
]

PROJECT_POOL = [
    {"title": "AI-Powered Crop Disease Detection Using UAV Imagery", "description": "Developing a deep learning pipeline (YOLOv8 + segmentation) to detect early-stage crop diseases from drone images. Dataset collected across Karnataka farms.", "funding_source": "SERB-DST", "funding_amount": "₹35 Lakhs", "status": "ongoing", "year_start": 2022, "year_end": None},
    {"title": "Blockchain-Based Academic Credential Verification System", "description": "Designing a Hyperledger Fabric network for tamper-proof issuance and verification of academic certificates across Indian universities.", "funding_source": "Ministry of Education (MoE)", "funding_amount": "₹28 Lakhs", "status": "completed", "year_start": 2021, "year_end": 2023},
    {"title": "Smart Grid Energy Management Using Multi-Agent Reinforcement Learning", "description": "Applying MARL to optimise load balancing and peak-demand shaving in a heterogeneous smart-grid testbed.", "funding_source": "DRDO", "funding_amount": "₹52 Lakhs", "status": "ongoing", "year_start": 2023, "year_end": None},
    {"title": "Low-Cost Wearable ECG Monitor with Edge-AI Arrhythmia Detection", "description": "Designed a BLE-enabled ECG patch with a TinyML model for real-time arrhythmia classification, achieving 94% accuracy.", "funding_source": "BIRAC (Dept. of Biotechnology)", "funding_amount": "₹18 Lakhs", "status": "completed", "year_start": 2020, "year_end": 2022},
    {"title": "Natural Language Interface for Government Service Portals (Kannada/Hindi)", "description": "Building a multilingual NLP chatbot using transformer models fine-tuned on Indic language corpora for citizen services.", "funding_source": "NIC (National Informatics Centre)", "funding_amount": "₹22 Lakhs", "status": "ongoing", "year_start": 2023, "year_end": None},
    {"title": "Seismic Performance Assessment of RC Buildings in Seismic Zone III", "description": "Non-linear pushover and time-history analyses of existing RC frames; fragility curve development for risk assessment.", "funding_source": "National Disaster Management Authority", "funding_amount": "₹15 Lakhs", "status": "completed", "year_start": 2019, "year_end": 2021},
    {"title": "Federated Learning Framework for Privacy-Preserving Healthcare Analytics", "description": "Implemented a cross-silo federated learning system across three hospital datasets without sharing raw patient data.", "funding_source": "ICMR", "funding_amount": "₹40 Lakhs", "status": "ongoing", "year_start": 2022, "year_end": None},
    {"title": "Intelligent Traffic Signal Control Using Computer Vision & Reinforcement Learning", "description": "Real-time vehicle density estimation from CCTV feeds to dynamically optimise signal timings; deployed at 4 junctions in pilot.", "funding_source": "Bruhat Bengaluru Mahanagara Palike (BBMP)", "funding_amount": "₹12 Lakhs", "status": "completed", "year_start": 2021, "year_end": 2023},
    {"title": "Microplastic Detection in Water Bodies Using Hyperspectral Imaging", "description": "Combining drone-mounted hyperspectral cameras with ML classification to map microplastic contamination in lakes.", "funding_source": "Karnataka State Pollution Control Board", "funding_amount": "₹10 Lakhs", "status": "ongoing", "year_start": 2023, "year_end": None},
    {"title": "Design and Fabrication of a Hydrogen-Fuelled Micro Gas Turbine", "description": "Experimental investigation of combustion characteristics of H2-CH4 blends in a 5 kW micro gas turbine; CFD validated.", "funding_source": "MNRE (Ministry of New & Renewable Energy)", "funding_amount": "₹45 Lakhs", "status": "ongoing", "year_start": 2022, "year_end": None},
    {"title": "Automated Software Vulnerability Scanner Using Static Analysis & LLMs", "description": "Tool that combines tree-sitter AST parsing with an LLM to detect CWE patterns in C/C++ and Python codebases.", "funding_source": "NASSCOM Foundation", "funding_amount": "₹8 Lakhs", "status": "completed", "year_start": 2022, "year_end": 2024},
    {"title": "High-Performance RISC-V SoC for Edge AI Inference", "description": "Custom RISC-V processor with integrated tensor acceleration unit; synthesised on Xilinx UltraScale+.", "funding_source": "C-DAC (Centre for Development of Advanced Computing)", "funding_amount": "₹60 Lakhs", "status": "ongoing", "year_start": 2023, "year_end": None},
    {"title": "Optimal Placement of Electric Vehicle Charging Stations in Urban Areas", "description": "Integer programming model incorporating travel demand, grid capacity, and land use to plan EV infrastructure.", "funding_source": "Ministry of Power", "funding_amount": "₹20 Lakhs", "status": "completed", "year_start": 2020, "year_end": 2022},
    {"title": "Gamified Learning Platform for K-12 STEM Education in Rural Schools", "description": "Designed an offline-first progressive web app with adaptive difficulty and Hindi/Kannada localisation.", "funding_source": "Google.org Social Impact Grant", "funding_amount": "₹25 Lakhs", "status": "ongoing", "year_start": 2023, "year_end": None},
    {"title": "Structural Health Monitoring of Bridges Using IoT Sensor Networks", "description": "Deployed a wireless sensor mesh on two bridges; anomaly detection via LSTM-based time-series models.", "funding_source": "National Highways Authority of India (NHAI)", "funding_amount": "₹30 Lakhs", "status": "completed", "year_start": 2020, "year_end": 2023},
]

COURSE_POOL = [
    {"name": "Data Structures & Algorithms", "students_count": 65},
    {"name": "Design & Analysis of Algorithms", "students_count": 58},
    {"name": "Operating Systems", "students_count": 72},
    {"name": "Database Management Systems", "students_count": 68},
    {"name": "Computer Networks", "students_count": 60},
    {"name": "Object-Oriented Programming with Java", "students_count": 80},
    {"name": "Compiler Design", "students_count": 52},
    {"name": "Artificial Intelligence", "students_count": 55},
    {"name": "Machine Learning", "students_count": 50},
    {"name": "Deep Learning & Neural Networks", "students_count": 45},
    {"name": "Software Engineering & Project Management", "students_count": 70},
    {"name": "Web Technologies", "students_count": 75},
    {"name": "Cloud Computing", "students_count": 48},
    {"name": "Information Security", "students_count": 55},
    {"name": "Digital Signal Processing", "students_count": 60},
    {"name": "Microprocessors & Microcontrollers", "students_count": 65},
    {"name": "VLSI Design", "students_count": 48},
    {"name": "Control Systems", "students_count": 62},
    {"name": "Signals & Systems", "students_count": 70},
    {"name": "Embedded Systems", "students_count": 52},
    {"name": "Engineering Mathematics I", "students_count": 90},
    {"name": "Engineering Mathematics II", "students_count": 88},
    {"name": "Engineering Mathematics III", "students_count": 75},
    {"name": "Probability & Statistics", "students_count": 80},
    {"name": "Discrete Mathematics", "students_count": 68},
    {"name": "Thermodynamics", "students_count": 72},
    {"name": "Fluid Mechanics", "students_count": 65},
    {"name": "Strength of Materials", "students_count": 60},
    {"name": "CAD/CAM", "students_count": 55},
    {"name": "Heat & Mass Transfer", "students_count": 58},
    {"name": "Structural Analysis", "students_count": 62},
    {"name": "Geotechnical Engineering", "students_count": 54},
    {"name": "Environmental Engineering", "students_count": 50},
    {"name": "Transportation Engineering", "students_count": 56},
    {"name": "Big Data Analytics", "students_count": 45},
    {"name": "Natural Language Processing", "students_count": 42},
    {"name": "Computer Vision", "students_count": 40},
    {"name": "Internet of Things", "students_count": 55},
    {"name": "Blockchain Technology", "students_count": 38},
]

SEMESTERS = ["Odd Sem (2021–22)", "Even Sem (2021–22)", "Odd Sem (2022–23)",
             "Even Sem (2022–23)", "Odd Sem (2023–24)", "Even Sem (2023–24)",
             "Odd Sem (2024–25)", "Even Sem (2024–25)"]
LECTURE_YEARS = [2020, 2021, 2021, 2022, 2022, 2023, 2023, 2024]
LECTURE_SEMS = ["Odd Sem", "Even Sem", "Annual Fest", "National Conference",
                "Workshop", "FDP", "Guest Lecture Series"]


def _pick(pool, index, count):
    """Pick `count` distinct items from pool starting at a deterministic offset."""
    n = len(pool)
    return [pool[(index + i) % n] for i in range(count)]


def _build_lectures(idx):
    count = 3 if idx % 3 == 0 else (4 if idx % 3 == 1 else 2)
    items = _pick(LECTURE_POOL, idx * 3, count)
    result = []
    for i, item in enumerate(items):
        result.append({
            "subject": item["subject"],
            "year": LECTURE_YEARS[(idx + i) % len(LECTURE_YEARS)],
            "semester": LECTURE_SEMS[(idx + i) % len(LECTURE_SEMS)],
            "details": item["details"],
        })
    return result


def _build_projects(idx):
    count = 2 if idx % 3 == 0 else (1 if idx % 3 == 1 else 2)
    items = _pick(PROJECT_POOL, idx * 2, count)
    return [dict(item) for item in items]


def _build_courses(idx):
    count = 3 if idx % 4 == 0 else (4 if idx % 4 == 1 else (2 if idx % 4 == 2 else 3))
    items = _pick(COURSE_POOL, idx * 5, count)
    result = []
    for i, item in enumerate(items):
        sem_offset = (idx + i) % len(SEMESTERS)
        result.append({
            "name": item["name"],
            "year": 2021 + (sem_offset // 2),
            "semester": SEMESTERS[sem_offset],
            "students_count": item["students_count"],
        })
    return result


def _years_exp(designation, idx):
    base = {"professor": 18, "associate_professor": 12, "assistant_professor": 5, "staff": 3}
    d = designation.value if designation else None
    b = base.get(d, 8)
    return b + (idx % 5)


def _bio(name, designation, years):
    d_label = {
        "professor": "Professor",
        "associate_professor": "Associate Professor",
        "assistant_professor": "Assistant Professor",
        "staff": "Staff Member",
    }.get(designation.value if designation else "", "Faculty Member")
    domains = [
        "machine learning and data science",
        "embedded systems and IoT",
        "computer networks and security",
        "VLSI design and verification",
        "structural engineering and analysis",
        "renewable energy systems",
        "natural language processing",
        "cloud computing and DevOps",
        "computer vision and image processing",
        "signal processing and communications",
    ]
    domain = domains[hash(name) % len(domains)]
    return (
        f"{name} is a {d_label} with over {years} years of teaching and research experience, "
        f"specialising in {domain}. They have published extensively in peer-reviewed journals and "
        f"conferences, guided multiple M.Tech and Ph.D. students, and have received grants from "
        f"funding agencies including DST, SERB, and DRDO."
    )


async def seed_profiles():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(
                User.role.in_([UserRole.FACULTY, UserRole.HOD]),
                User.is_active == True,
            )
        )
        users = result.scalars().all()
        print(f"Found {len(users)} faculty/HoD users")

        new_count = 0
        update_count = 0

        for rank, user in enumerate(users):
            existing = (await db.execute(
                select(FacultyProfile).where(FacultyProfile.user_id == user.id)
            )).scalar_one_or_none()

            yrs = _years_exp(user.designation, rank)
            bio = _bio(user.name, user.designation, yrs)
            lectures = _build_lectures(rank)
            projects = _build_projects(rank)
            courses = _build_courses(rank)

            if existing:
                existing.years_experience = yrs
                existing.bio = bio
                existing.lectures_json = json.dumps(lectures)
                existing.projects_json = json.dumps(projects)
                existing.courses_json = json.dumps(courses)
                update_count += 1
            else:
                db.add(FacultyProfile(
                    user_id=user.id,
                    years_experience=yrs,
                    bio=bio,
                    lectures_json=json.dumps(lectures),
                    projects_json=json.dumps(projects),
                    courses_json=json.dumps(courses),
                ))
                new_count += 1

            print(f"  {'UPDATE' if existing else 'INSERT'} profile for {user.name} ({user.role.value})")

        await db.commit()
        print(f"\nDone — {new_count} inserted, {update_count} updated.")


if __name__ == "__main__":
    asyncio.run(seed_profiles())
