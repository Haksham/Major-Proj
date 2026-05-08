# SALF API Documentation

## Overview

The SALF (Secure Academic Ledger Framework) API provides endpoints for managing academic contributions, evaluations, and credit portfolios. All endpoints are RESTful and return JSON responses.

## Base URL

- Development: `http://localhost:8000/api/v1`
- Production: `https://your-domain.com/api/v1`

## Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

### Wallet Authentication Flow

1. User connects MetaMask wallet
2. Frontend requests nonce from `/auth/nonce`
3. User signs nonce with MetaMask
4. Frontend sends signature to `/auth/verify`
5. Backend verifies signature and issues JWT

---

## Endpoints

### Authentication

#### POST `/auth/nonce`

Get a nonce for wallet authentication.

**Request Body:**

```json
{
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f..."
}
```

**Response:**

```json
{
  "nonce": "Sign this message to authenticate: abc123...",
  "expires_at": "2024-01-15T10:00:00Z"
}
```

#### POST `/auth/verify`

Verify signed message and get JWT token.

**Request Body:**

```json
{
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f...",
  "signature": "0x..."
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "wallet_address": "0x...",
    "role": "faculty",
    "full_name": "Dr. John Doe"
  }
}
```

#### GET `/auth/me`

Get current user profile. **Requires authentication.**

**Response:**

```json
{
  "id": "uuid",
  "wallet_address": "0x...",
  "employee_id": "EMP001",
  "full_name": "Dr. John Doe",
  "email": "john.doe@university.edu",
  "department": "Computer Science",
  "designation": "Associate Professor",
  "role": "faculty"
}
```

---

### Contributions

#### GET `/contributions`

Get contributions with optional filters. **Requires authentication.**

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by status (pending, under_review, evaluated, approved, rejected) |
| category | string | Filter by contribution category |
| from_date | date | Filter from date |
| to_date | date | Filter to date |
| page | int | Page number (default: 1) |
| limit | int | Items per page (default: 20) |

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Machine Learning in Healthcare",
      "category": "JOURNAL_PAPER",
      "status": "approved",
      "base_points": 25,
      "final_credits": 32.5,
      "quality_score": 85.5,
      "submission_date": "2024-01-10T09:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "pages": 3
}
```

#### POST `/contributions/submit`

Submit a new contribution with a PDF upload. **Requires authentication (Faculty).**

**Content-Type:** `multipart/form-data`

**Form Fields:**
| Field | Type | Required | Notes |
|------|------|----------|------|
| category | string | yes | One of: `refereed_journal`, `international_book`, `national_book`, `book_chapter`, `international_lecture`, `national_conference`, `patent_filed`, `patent_granted`, `editorial_work`, `research_project` |
| title | string | yes |  |
| abstract | string | yes | Minimum 100 characters |
| journal_name | string | no |  |
| isbn | string | no |  |
| issn | string | no |  |
| doi | string | no |  |
| co_authors | string | no | Comma-separated names |
| file | file | yes | PDF only |

**Response:**

```json
{
  "id": 1,
  "blockchain_id": 1,
  "faculty_id": 1,
  "category": "refereed_journal",
  "title": "Novel Approach to Deep Learning",
  "abstract": "…",
  "ipfs_hash": "Qm…",
  "status": "pending"
}
```

#### GET `/contributions/{id}`

Get contribution details. **Requires authentication.**

**Response:**

```json
{
  "id": "uuid",
  "title": "Novel Approach to Deep Learning",
  "category": "JOURNAL_PAPER",
  "description": "This paper presents...",
  "status": "approved",
  "base_points": 25,
  "quality_score": 88.5,
  "novelty_score": 75.2,
  "final_credits": 34.8,
  "ipfs_hash": "Qm...",
  "blockchain_id": "0x...",
  "metadata": {},
  "evaluation": {
    "category_scores": {
      "research_quality": 90.5,
      "academic_impact": 85.0,
      "writing_quality": 88.0,
      "innovation": 82.5
    },
    "comments": "Excellent research contribution",
    "evaluated_by": "Dr. Reviewer"
  }
}
```

---

### Portfolio

#### GET `/portfolio`

Get current user's credit portfolio. **Requires authentication.**

**Response:**

```json
{
  "faculty_id": "uuid",
  "total_credits": 245.5,
  "breakdown": {
    "journal_credits": 100.0,
    "book_credits": 50.0,
    "patent_credits": 50.0,
    "conference_credits": 25.5,
    "project_credits": 20.0
  },
  "contributions_count": 15,
  "pending_count": 2,
  "last_updated": "2024-01-15T10:00:00Z"
}
```

#### GET `/portfolio/history`

Get credit history over time. **Requires authentication.**

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| period | string | time period: month, quarter, year |

**Response:**

```json
{
  "history": [
    { "date": "2024-01", "credits": 45.5, "contributions": 3 },
    { "date": "2023-12", "credits": 30.0, "contributions": 2 }
  ]
}
```

#### GET `/portfolio/export`

Export portfolio data. **Requires authentication.**

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| format | string | Export format: pdf, csv, json |

---

### Reviews (HoD/Reviewer)

#### GET `/reviews/pending`

Get pending contributions for review. **Requires HoD/Reviewer role.**

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "faculty_name": "Dr. John Doe",
      "title": "Contribution Title",
      "category": "JOURNAL_PAPER",
      "submission_date": "2024-01-10T09:00:00Z",
      "ai_evaluation": {
        "quality_score": 85.5,
        "novelty_score": 72.0,
        "fraud_check_passed": true
      }
    }
  ]
}
```

#### POST `/reviews/{contribution_id}/evaluate`

Submit manual evaluation. **Requires HoD/Reviewer role.**

**Request Body:**

```json
{
  "quality_score": 88.0,
  "comments": "Excellent contribution with significant impact",
  "recommendation": "approve"
}
```

**Response:**

```json
{
  "contribution_id": "uuid",
  "status": "approved",
  "final_credits": 34.8,
  "message": "Evaluation submitted and recorded on blockchain"
}
```

---

### Admin

#### GET `/admin/dashboard`

Get admin dashboard statistics. **Requires Admin role.**

**Response:**

```json
{
  "total_faculty": 150,
  "total_contributions": 1250,
  "pending_reviews": 45,
  "total_credits_issued": 12500.5,
  "contributions_this_month": 85,
  "top_contributors": [{ "name": "Dr. Jane Smith", "credits": 450.5 }],
  "category_breakdown": {
    "JOURNAL_PAPER": 500,
    "PATENT_GRANTED": 50
  }
}
```

#### GET `/admin/users`

Get all users. **Requires Admin role.**

#### POST `/admin/users`

Create new user. **Requires Admin role.**

#### PUT `/admin/users/{id}/role`

Update user role. **Requires Admin role.**

---

## Error Responses

All errors follow this format:

```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "Human readable error message"
  }
}
```

### Common Error Codes

| Code             | HTTP Status | Description                       |
| ---------------- | ----------- | --------------------------------- |
| UNAUTHORIZED     | 401         | Invalid or missing authentication |
| FORBIDDEN        | 403         | Insufficient permissions          |
| NOT_FOUND        | 404         | Resource not found                |
| VALIDATION_ERROR | 422         | Invalid request data              |
| BLOCKCHAIN_ERROR | 500         | Blockchain transaction failed     |
| IPFS_ERROR       | 500         | IPFS upload/retrieval failed      |

---

## Rate Limiting

- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated endpoints

---

## WebSocket Events

Connect to `ws://localhost:8000/ws` for real-time updates.

### Events

- `contribution:submitted` - New contribution submitted
- `contribution:evaluated` - Contribution evaluated
- `contribution:approved` - Contribution approved
- `credits:updated` - User credits updated

---

## Blockchain Integration

All approved contributions are recorded on-chain with:

- Transaction hash stored in `blockchain_id`
- Document hash stored on IPFS (`ipfs_hash`)
- Immutable credit records on Hyperledger Besu

---

## OpenAPI/Swagger

Interactive API documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
