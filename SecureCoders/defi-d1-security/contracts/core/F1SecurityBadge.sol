// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title F1SecurityBadge
 * @dev NFT badges for gamification - reward users for secure transactions
 */
contract F1SecurityBadge is ERC721, ERC721URIStorage, Ownable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIdCounter;
    
    // Badge levels (F1 themed)
    enum BadgeLevel { 
        Rookie,      // 0 - 10 safe transactions
        Driver,      // 10 - 50 safe transactions
        Champion,    // 50 - 100 safe transactions
        Legend       // 100+ safe transactions
    }
    
    // Mapping from user to their stats
    mapping(address => uint256) public safeTransactions;
    mapping(address => uint256) public securityScore;
    mapping(uint256 => BadgeLevel) public tokenBadgeLevel;
    mapping(address => uint256[]) public userBadges;
    
    // Badge URI templates (IPFS or centralized storage)
    mapping(BadgeLevel => string) public badgeURIs;
    
    // Events
    event BadgeEarned(address indexed user, uint256 tokenId, BadgeLevel level);
    event SafeTransactionRecorded(address indexed user, uint256 newScore);
    
    constructor() ERC721("F1SecurityBadge", "F1SB") Ownable(msg.sender) {
        // Set default badge URIs (update with actual IPFS links)
        badgeURIs[BadgeLevel.Rookie] = "ipfs://QmRookieBadge";
        badgeURIs[BadgeLevel.Driver] = "ipfs://QmDriverBadge";
        badgeURIs[BadgeLevel.Champion] = "ipfs://QmChampionBadge";
        badgeURIs[BadgeLevel.Legend] = "ipfs://QmLegendBadge";
    }
    
    /**
     * @dev Record a safe transaction and potentially mint badge
     */
    function recordSafeTransaction(address user) external onlyOwner {
        safeTransactions[user]++;
        securityScore[user] += 10;
        
        emit SafeTransactionRecorded(user, securityScore[user]);
        
        // Check if user earned a new badge
        _checkAndMintBadge(user);
    }
    
    /**
     * @dev Internal function to check badge eligibility and mint
     */
    function _checkAndMintBadge(address user) internal {
        uint256 txCount = safeTransactions[user];
        
        if (txCount == 10) {
            _mintBadge(user, BadgeLevel.Rookie);
        } else if (txCount == 50) {
            _mintBadge(user, BadgeLevel.Driver);
        } else if (txCount == 100) {
            _mintBadge(user, BadgeLevel.Champion);
        } else if (txCount == 200) {
            _mintBadge(user, BadgeLevel.Legend);
        }
    }
    
    /**
     * @dev Mint a badge NFT to user
     */
    function _mintBadge(address to, BadgeLevel level) internal {
        _tokenIdCounter.increment();
        uint256 tokenId = _tokenIdCounter.current();
        
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, badgeURIs[level]);
        
        tokenBadgeLevel[tokenId] = level;
        userBadges[to].push(tokenId);
        
        emit BadgeEarned(to, tokenId, level);
    }
    
    /**
     * @dev Get user's badge collection
     */
    function getUserBadges(address user) external view returns (uint256[] memory) {
        return userBadges[user];
    }
    
    /**
     * @dev Update badge URI (only owner)
     */
    function setBadgeURI(BadgeLevel level, string memory uri) external onlyOwner {
        badgeURIs[level] = uri;
    }
    
    // Required overrides
    function tokenURI(uint256 tokenId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (string memory)
    {
        return super.tokenURI(tokenId);
    }
    
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
    
    function _burn(uint256 tokenId) internal override(ERC721, ERC721URIStorage) {
        super._burn(tokenId);
    }
}
