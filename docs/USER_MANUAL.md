# SALF User Manual

## Secure Academic Ledger Framework - User Guide

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Faculty Guide](#faculty-guide)
4. [Head of Department (HoD) Guide](#head-of-department-hod-guide)
5. [Administrator Guide](#administrator-guide)
6. [Troubleshooting](#troubleshooting)

---

## Introduction

SALF (Secure Academic Ledger Framework) is a blockchain-based platform for managing and validating academic contributions of faculty members. The system provides:

- **Immutable Records**: All contributions are stored on blockchain
- **AI-Powered Evaluation**: Automatic quality and novelty scoring
- **UGC Credit Mapping**: Credits aligned with University Grants Commission guidelines
- **Fraud Detection**: ML-based plagiarism and anomaly detection
- **Inter-Institutional Portability**: Transfer credits between institutions

### Contribution Categories

| Category                 | Base Points | Description                               |
| ------------------------ | ----------- | ----------------------------------------- |
| Research Journal Paper   | 25          | UGC-CARE listed publication               |
| International Book       | 30          | ISBN-registered international publication |
| National Book            | 20          | ISBN-registered national publication      |
| Patent Granted           | 50          | Approved patent (national/international)  |
| Patent Filed             | 25          | Patent application submitted              |
| International Conference | 15          | Paper at international conference         |
| National Conference      | 10          | Paper at national conference              |
| Major Research Project   | 40          | Funded project (>10 lakhs)                |
| Minor Research Project   | 20          | Small funded project                      |
| Consultancy              | 30          | Industry consultancy                      |

### Credit Formula

```
Final Credits = Base Points × (1 + Quality Score/100) × (1 + Novelty Multiplier)
```

---

## Getting Started

### Prerequisites

1. **MetaMask Wallet**: Install from [metamask.io](https://metamask.io)
2. **Modern Browser**: Chrome, Firefox, or Edge (latest version)
3. **Institution Registration**: Your wallet must be registered by admin

### Connecting Your Wallet

1. Click "Connect Wallet" on the login page
2. MetaMask will prompt you to connect
3. Select your registered wallet address
4. Sign the authentication message
5. You'll be redirected to your dashboard

### Network Configuration

Add the SALF network to MetaMask:

- Network Name: SALF Network
- RPC URL: (provided by your institution)
- Chain ID: 1337
- Currency: ETH

---

## Faculty Guide

### Dashboard Overview

Your dashboard shows:

- **Total Credits**: Your accumulated academic credits
- **Contribution Stats**: Total, approved, pending, rejected
- **Credit History**: Graph showing credit growth over time
- **Recent Activity**: Latest contribution updates

### Submitting a Contribution

1. Navigate to **Contributions** → **Submit New**
2. Select contribution category
3. Fill in required information:
   - Title
   - Description/Abstract
   - Publication details (journal name, DOI, ISBN, etc.)
4. Upload supporting documents (PDF, max 10MB)
5. Click **Submit**
6. Sign the blockchain transaction in MetaMask

### Required Information by Category

**Journal Paper:**

- Journal name
- ISSN number
- Publication date
- DOI (if available)
- Co-author list

**Book Publication:**

- ISBN
- Publisher name
- Publication year
- Chapter contributions (if applicable)

**Patent:**

- Patent number (if granted)
- Application number
- Filing date
- Inventor list

**Conference Paper:**

- Conference name
- Location
- Dates
- Paper ID/DOI

**Research Project:**

- Funding agency
- Project duration
- Sanctioned amount
- Project ID

### Tracking Your Submissions

View all submissions in **Contributions** page:

- **Pending**: Awaiting evaluation
- **Under Review**: Being reviewed by HoD
- **Evaluated**: AI evaluation complete
- **Approved**: Credits awarded
- **Rejected**: Not accepted (with reason)

### Viewing Your Portfolio

Your portfolio shows:

- Total credits by category
- Contribution history
- Credit growth chart
- Exportable reports (PDF/CSV)

### Downloading Certificates

For approved contributions:

1. Go to **Contributions**
2. Click on approved contribution
3. Click **Download Certificate**
4. Certificate includes blockchain verification QR code

---

## Head of Department (HoD) Guide

### Additional Responsibilities

As HoD, you can:

- Review and approve faculty contributions
- Override AI evaluations
- View department statistics
- Generate department reports

### Reviewing Contributions

1. Go to **Reviews** page
2. View pending contributions from your department
3. Each entry shows:
   - Faculty name
   - Contribution details
   - AI-generated scores
   - Fraud detection status

### Evaluation Process

1. Click on a contribution to review
2. View AI evaluation:
   - Quality Score (0-100)
   - Novelty Score (0-100)
   - Category scores breakdown
3. Review supporting documents
4. Enter your assessment:
   - Adjust quality score if needed
   - Add comments
5. Select action:
   - **Approve**: Award credits
   - **Reject**: Deny with reason
   - **Request Revision**: Ask for changes
6. Sign blockchain transaction

### Department Dashboard

View:

- Total faculty contributions
- Average quality scores
- Top contributors
- Monthly/quarterly trends

---

## Administrator Guide

### System Management

Administrators can:

- Manage user accounts
- Configure departments
- Set system parameters
- View system-wide analytics
- Handle inter-institutional transfers

### User Management

**Creating Users:**

1. Go to **Admin Panel** → **Users**
2. Click **Add User**
3. Enter:
   - Wallet address
   - Employee ID
   - Full name
   - Email
   - Department
   - Role (Faculty/HoD/Admin)
4. User receives notification to connect

**Modifying Roles:**

1. Find user in list
2. Click **Edit**
3. Change role as needed
4. Changes reflect immediately

### Department Management

1. Go to **Admin Panel** → **Departments**
2. Create/edit departments
3. Assign HoDs

### System Analytics

**Dashboard shows:**

- Total users and contributions
- Credit distribution
- Fraud detection statistics
- System health metrics

**Reports available:**

- Monthly contribution reports
- Department-wise analysis
- Category-wise breakdown
- Export to PDF/Excel

### Blockchain Operations

**Contract Management:**

- View contract addresses
- Monitor gas usage
- Check transaction history

**Emergency Controls:**

- Pause system (security issues)
- Blacklist users
- Freeze contributions

---

## Troubleshooting

### Common Issues

**"Wallet not connected"**

- Ensure MetaMask is installed and unlocked
- Check you're on correct network
- Try disconnecting and reconnecting

**"Transaction failed"**

- Check you have sufficient ETH for gas
- Network might be congested - try again
- Contact admin if persists

**"Contribution rejected"**

- Review rejection reason
- Ensure all required documents uploaded
- Contact HoD for clarification

**"Login failed"**

- Verify wallet address is registered
- Ensure signing the exact message
- Clear browser cache and retry

### Getting Help

- **Technical Issues**: Contact IT Support
- **Account Issues**: Contact Admin
- **Evaluation Questions**: Contact HoD
- **Policy Questions**: Contact Academic Office

### Security Best Practices

1. Never share your wallet private key
2. Use hardware wallet for large credit holdings
3. Verify transaction details before signing
4. Report suspicious activity immediately
5. Keep MetaMask updated

---

## Appendix

### Glossary

- **Blockchain**: Distributed, immutable ledger
- **IPFS**: Decentralized file storage
- **MetaMask**: Browser wallet for blockchain
- **Smart Contract**: Self-executing code on blockchain
- **Gas**: Transaction fee on blockchain
- **UGC**: University Grants Commission

### Contact Information

- System Admin: admin@institution.edu
- Technical Support: support@institution.edu
- Documentation: https://docs.salf.edu

---

_Version 1.0 | Last Updated: 2024_
