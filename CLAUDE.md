# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This is a documentation-focused repository containing API specifications for Korean e-commerce platforms:

```
/home/sunwoo/yooni/
└── module/
    └── supplier/
        └── ownerclan/
            └── docs/
                └── ownerclan-api-spec copy.md
```

## Content Overview

The repository contains Korean-language API documentation for the OwnerClan e-commerce platform, including:

- **GraphQL API Specification**: Complete API documentation for OwnerClan seller API v0.11.0
- **Authentication**: JWT-based authentication system
- **Endpoints**: Production and sandbox GraphQL endpoints
- **Data Types**: Comprehensive type definitions for products, orders, shipping, etc.
- **Usage Examples**: Query examples and response formats

## Key API Components

### Core Entities
- **Items**: Product management with options, pricing, categories, and inventory
- **Orders**: Order lifecycle management from creation to fulfillment
- **Shipping**: Delivery management with multiple shipping types

### Important Features
- **Multi-product orders**: Automatic order splitting based on vendor and shipping type
- **International shipping**: Special handling for overseas products with customs clearance
- **Return/Exchange**: Product return and exchange request functionality
- **Rate limiting**: 1000 requests per second for individual item queries

## Development Notes

- This is a documentation repository with no executable code
- All content is in Korean language
- Focus on API integration and e-commerce platform connectivity
- No build tools, test frameworks, or development dependencies present

## API Endpoints

- **Production**: `https://api.ownerclan.com/v1/graphql`
- **Sandbox**: `https://api-sandbox.ownerclan.com/v1/graphql`
- **Authentication**: `https://auth.ownerclan.com/auth` (production), `https://auth-sandbox.ownerclan.com/auth` (sandbox)