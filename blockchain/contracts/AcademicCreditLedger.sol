// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title AcademicCreditLedger
 * @notice Main contract for managing academic contributions and credits
 * @dev Implements the Secure Academic Ledger Framework (SALF)
 */
contract AcademicCreditLedger is AccessControl, Pausable, ReentrancyGuard {
    // Roles
    bytes32 public constant FACULTY_ROLE = keccak256("FACULTY_ROLE");
    bytes32 public constant HOD_ROLE = keccak256("HOD_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant REM_ROLE = keccak256("REM_ROLE");

    // Contribution categories with UGC base points
    enum ContributionCategory {
        REFEREED_JOURNAL,      // 25 points
        INTERNATIONAL_BOOK,    // 30 points
        NATIONAL_BOOK,         // 20 points
        BOOK_CHAPTER,          // 5 points
        INTERNATIONAL_LECTURE, // 7 points
        NATIONAL_CONFERENCE,   // 10 points
        PATENT_FILED,          // 15 points
        PATENT_GRANTED,        // 30 points
        EDITORIAL_WORK,        // 10 points
        RESEARCH_PROJECT       // 20 points
    }

    // Contribution status
    enum ContributionStatus {
        PENDING,
        UNDER_REVIEW,
        VALIDATED,
        REJECTED,
        FLAGGED
    }

    // UGC Base Points mapping
    mapping(ContributionCategory => uint256) public ugcBasePoints;

    // Contribution structure
    struct Contribution {
        uint256 id;
        address faculty;
        ContributionCategory category;
        string title;
        string ipfsHash;           // IPFS CID for the document
        string metadataHash;       // SHA-256 hash of metadata
        uint256 submissionTime;
        ContributionStatus status;
        uint256 aiQualityScore;    // 0-100 scale from REM
        uint256 noveltyPercentage; // 0-100 novelty score
        uint256 finalCredits;
        string reviewNotes;
        address reviewer;
        uint256 reviewTime;
    }

    // Benchmark attributes for AI evaluation (36 attributes)
    struct BenchmarkWeights {
        uint256 methodologyRigor;
        uint256 literatureReview;
        uint256 dataQuality;
        uint256 analysisDepth;
        uint256 conclusionStrength;
        uint256 citationImpact;
        uint256 reproducibility;
        uint256 practicalApplication;
        // Additional attributes represented as array
        uint256[28] additionalWeights;
    }

    // State variables
    uint256 public contributionCounter;
    BenchmarkWeights public benchmarkWeights;
    
    // Mappings
    mapping(uint256 => Contribution) public contributions;
    mapping(address => uint256[]) public facultyContributions;
    mapping(address => uint256) public facultyTotalCredits;
    mapping(string => bool) public ipfsHashExists;  // Prevent duplicates
    mapping(string => bool) public metadataHashExists;
    
    // Events
    event ContributionSubmitted(
        uint256 indexed contributionId,
        address indexed faculty,
        ContributionCategory category,
        string ipfsHash
    );
    event ContributionEvaluated(
        uint256 indexed contributionId,
        uint256 qualityScore,
        uint256 noveltyPercentage
    );
    event ContributionValidated(
        uint256 indexed contributionId,
        uint256 finalCredits,
        address reviewer
    );
    event ContributionRejected(
        uint256 indexed contributionId,
        string reason,
        address reviewer
    );
    event ContributionFlagged(
        uint256 indexed contributionId,
        string reason
    );
    event BenchmarkWeightsUpdated(address admin);
    event FacultyCreditsUpdated(address indexed faculty, uint256 newTotal);

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
        
        // Initialize UGC base points
        ugcBasePoints[ContributionCategory.REFEREED_JOURNAL] = 25;
        ugcBasePoints[ContributionCategory.INTERNATIONAL_BOOK] = 30;
        ugcBasePoints[ContributionCategory.NATIONAL_BOOK] = 20;
        ugcBasePoints[ContributionCategory.BOOK_CHAPTER] = 5;
        ugcBasePoints[ContributionCategory.INTERNATIONAL_LECTURE] = 7;
        ugcBasePoints[ContributionCategory.NATIONAL_CONFERENCE] = 10;
        ugcBasePoints[ContributionCategory.PATENT_FILED] = 15;
        ugcBasePoints[ContributionCategory.PATENT_GRANTED] = 30;
        ugcBasePoints[ContributionCategory.EDITORIAL_WORK] = 10;
        ugcBasePoints[ContributionCategory.RESEARCH_PROJECT] = 20;
        
        // Initialize default benchmark weights
        _initializeBenchmarkWeights();
    }

    /**
     * @notice Initialize default benchmark weights
     */
    function _initializeBenchmarkWeights() internal {
        benchmarkWeights.methodologyRigor = 15;
        benchmarkWeights.literatureReview = 10;
        benchmarkWeights.dataQuality = 12;
        benchmarkWeights.analysisDepth = 13;
        benchmarkWeights.conclusionStrength = 10;
        benchmarkWeights.citationImpact = 15;
        benchmarkWeights.reproducibility = 10;
        benchmarkWeights.practicalApplication = 15;
        // Remaining 28 attributes initialized to 0 by default
    }

    /**
     * @notice Submit a new academic contribution
     * @param _category Type of contribution
     * @param _title Title of the work
     * @param _ipfsHash IPFS CID of the document
     * @param _metadataHash SHA-256 hash of document metadata
     */
    function submitRecord(
        ContributionCategory _category,
        string memory _title,
        string memory _ipfsHash,
        string memory _metadataHash
    ) external onlyRole(FACULTY_ROLE) whenNotPaused nonReentrant returns (uint256) {
        require(bytes(_ipfsHash).length > 0, "Invalid IPFS hash");
        require(bytes(_metadataHash).length > 0, "Invalid metadata hash");
        require(!ipfsHashExists[_ipfsHash], "Duplicate submission: IPFS hash exists");
        require(!metadataHashExists[_metadataHash], "Duplicate submission: Metadata hash exists");

        contributionCounter++;
        uint256 contributionId = contributionCounter;

        contributions[contributionId] = Contribution({
            id: contributionId,
            faculty: msg.sender,
            category: _category,
            title: _title,
            ipfsHash: _ipfsHash,
            metadataHash: _metadataHash,
            submissionTime: block.timestamp,
            status: ContributionStatus.PENDING,
            aiQualityScore: 0,
            noveltyPercentage: 0,
            finalCredits: 0,
            reviewNotes: "",
            reviewer: address(0),
            reviewTime: 0
        });

        facultyContributions[msg.sender].push(contributionId);
        ipfsHashExists[_ipfsHash] = true;
        metadataHashExists[_metadataHash] = true;

        emit ContributionSubmitted(contributionId, msg.sender, _category, _ipfsHash);

        return contributionId;
    }

    /**
     * @notice Record AI evaluation results (called by REM)
     * @param _contributionId Contribution ID
     * @param _qualityScore Quality score (0-100)
     * @param _noveltyPercentage Novelty percentage (0-100)
     */
    function recordEvaluation(
        uint256 _contributionId,
        uint256 _qualityScore,
        uint256 _noveltyPercentage
    ) external onlyRole(REM_ROLE) whenNotPaused {
        require(_contributionId <= contributionCounter && _contributionId > 0, "Invalid contribution ID");
        require(contributions[_contributionId].status == ContributionStatus.PENDING, "Not pending evaluation");
        require(_qualityScore <= 100, "Quality score must be <= 100");
        require(_noveltyPercentage <= 100, "Novelty percentage must be <= 100");

        Contribution storage contribution = contributions[_contributionId];
        contribution.aiQualityScore = _qualityScore;
        contribution.noveltyPercentage = _noveltyPercentage;
        contribution.status = ContributionStatus.UNDER_REVIEW;

        emit ContributionEvaluated(_contributionId, _qualityScore, _noveltyPercentage);
    }

    /**
     * @notice Validate and finalize contribution credits
     * @param _contributionId Contribution ID
     * @param _notes Review notes
     */
    function validateBlock(
        uint256 _contributionId,
        string memory _notes
    ) external onlyRole(HOD_ROLE) whenNotPaused nonReentrant {
        require(_contributionId <= contributionCounter && _contributionId > 0, "Invalid contribution ID");
        Contribution storage contribution = contributions[_contributionId];
        require(contribution.status == ContributionStatus.UNDER_REVIEW, "Not under review");

        // Calculate final credits using formula:
        // FinalCredits = BasePoints × (1 + QualityScore/100) × (1 + NoveltyMultiplier)
        uint256 basePoints = ugcBasePoints[contribution.category];
        uint256 qualityMultiplier = 100 + contribution.aiQualityScore;
        uint256 noveltyMultiplier = 100 + (contribution.noveltyPercentage / 2); // Novelty adds up to 50% bonus
        
        // Calculate final credits (divided by 10000 to normalize)
        uint256 finalCredits = (basePoints * qualityMultiplier * noveltyMultiplier) / 10000;
        
        contribution.finalCredits = finalCredits;
        contribution.status = ContributionStatus.VALIDATED;
        contribution.reviewNotes = _notes;
        contribution.reviewer = msg.sender;
        contribution.reviewTime = block.timestamp;

        // Update faculty total credits
        facultyTotalCredits[contribution.faculty] += finalCredits;

        emit ContributionValidated(_contributionId, finalCredits, msg.sender);
        emit FacultyCreditsUpdated(contribution.faculty, facultyTotalCredits[contribution.faculty]);
    }

    /**
     * @notice Reject a contribution
     * @param _contributionId Contribution ID
     * @param _reason Rejection reason
     */
    function rejectContribution(
        uint256 _contributionId,
        string memory _reason
    ) external onlyRole(HOD_ROLE) whenNotPaused {
        require(_contributionId <= contributionCounter && _contributionId > 0, "Invalid contribution ID");
        Contribution storage contribution = contributions[_contributionId];
        require(
            contribution.status == ContributionStatus.PENDING || 
            contribution.status == ContributionStatus.UNDER_REVIEW,
            "Cannot reject"
        );

        contribution.status = ContributionStatus.REJECTED;
        contribution.reviewNotes = _reason;
        contribution.reviewer = msg.sender;
        contribution.reviewTime = block.timestamp;

        emit ContributionRejected(_contributionId, _reason, msg.sender);
    }

    /**
     * @notice Flag a suspicious contribution
     * @param _contributionId Contribution ID
     * @param _reason Flag reason
     */
    function flagContribution(
        uint256 _contributionId,
        string memory _reason
    ) external whenNotPaused {
        require(
            hasRole(HOD_ROLE, msg.sender) || hasRole(REM_ROLE, msg.sender),
            "Unauthorized"
        );
        require(_contributionId <= contributionCounter && _contributionId > 0, "Invalid contribution ID");
        
        Contribution storage contribution = contributions[_contributionId];
        contribution.status = ContributionStatus.FLAGGED;
        contribution.reviewNotes = _reason;

        emit ContributionFlagged(_contributionId, _reason);
    }

    /**
     * @notice Get contribution details
     * @param _contributionId Contribution ID
     */
    function getContribution(uint256 _contributionId) external view returns (Contribution memory) {
        require(_contributionId <= contributionCounter && _contributionId > 0, "Invalid contribution ID");
        return contributions[_contributionId];
    }

    /**
     * @notice Get all contributions for a faculty member
     * @param _faculty Faculty address
     */
    function getFacultyContributions(address _faculty) external view returns (uint256[] memory) {
        return facultyContributions[_faculty];
    }

    /**
     * @notice Get faculty total credits
     * @param _faculty Faculty address
     */
    function getFacultyTotalCredits(address _faculty) external view returns (uint256) {
        return facultyTotalCredits[_faculty];
    }

    /**
     * @notice Get Academic Credit Portfolio summary
     * @param _faculty Faculty address
     */
    function getAcademicPortfolio(address _faculty) external view returns (
        uint256 totalCredits,
        uint256 totalContributions,
        uint256 validatedCount,
        uint256 pendingCount,
        uint256 rejectedCount
    ) {
        totalCredits = facultyTotalCredits[_faculty];
        uint256[] memory contribIds = facultyContributions[_faculty];
        totalContributions = contribIds.length;

        for (uint256 i = 0; i < contribIds.length; i++) {
            ContributionStatus status = contributions[contribIds[i]].status;
            if (status == ContributionStatus.VALIDATED) {
                validatedCount++;
            } else if (status == ContributionStatus.PENDING || status == ContributionStatus.UNDER_REVIEW) {
                pendingCount++;
            } else if (status == ContributionStatus.REJECTED) {
                rejectedCount++;
            }
        }
    }

    /**
     * @notice Update UGC base points for a category
     * @param _category Contribution category
     * @param _points New base points
     */
    function updateUGCBasePoints(
        ContributionCategory _category,
        uint256 _points
    ) external onlyRole(ADMIN_ROLE) {
        ugcBasePoints[_category] = _points;
    }

    /**
     * @notice Update benchmark weights
     * @param _weights New benchmark weights
     */
    function updateBenchmarkWeights(
        BenchmarkWeights calldata _weights
    ) external onlyRole(ADMIN_ROLE) {
        benchmarkWeights = _weights;
        emit BenchmarkWeightsUpdated(msg.sender);
    }

    /**
     * @notice Pause the contract
     */
    function pause() external onlyRole(ADMIN_ROLE) {
        _pause();
    }

    /**
     * @notice Unpause the contract
     */
    function unpause() external onlyRole(ADMIN_ROLE) {
        _unpause();
    }

    /**
     * @notice Get total number of contributions
     */
    function getTotalContributions() external view returns (uint256) {
        return contributionCounter;
    }
}
