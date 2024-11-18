# Email Client Single-Page Application PRD

## Overview
This document outlines the product requirements for a single-page email client application built using JavaScript, HTML, and CSS. The core functionality will be implemented in `inbox.js`.

## Core Features

### 1. Email Management
#### 1.1 Mailbox Views
- **Inbox View**
  - Display emails with sender, subject line, and timestamp
  - Unread emails: White background
  - Read emails: Gray background
  - Auto-refresh on visit to show latest emails
  - Display mailbox name at top of page

- **Sent Mailbox**
  - Similar display format as inbox
  - Show outgoing email details

- **Archive**
  - Similar display format as inbox
  - Store archived emails separately

#### 1.2 Email Composition
- **Send Email**
  - POST request to `/emails` endpoint
  - Required fields: recipients, subject, body
  - Redirect to sent mailbox after successful send

### 2. Email Interaction
#### 2.1 Email Viewing
- **Detailed View**
  - Display full email content:
    - Sender
    - Recipients
    - Subject
    - Timestamp
    - Body
  - Mark as read automatically upon opening
  - Implement via GET request to `/emails/<email_id>`

#### 2.2 Email Actions
- **Archive Management**
  - Archive button for inbox emails
  - Unarchive button for archived emails
  - Exclude sent emails from archiving
  - Redirect to inbox after action
  - Implementation: PUT request to `/emails/<email_id>`

- **Reply Functionality**
  - Reply button in email view
  - Auto-populated composition form:
    - Recipient: Original sender
    - Subject: Add "Re: " prefix (if not present)
    - Body: Include original email quote with timestamp

## Technical Requirements
- Single-page application architecture
- All functionality must be implemented in `inbox.js`
- RESTful API integration for all email operations
- Dynamic DOM manipulation for view switching
- Event listener implementation for user interactions

## API Endpoints
- GET `/emails/<mailbox>`: Retrieve mailbox emails
- GET `/emails/<email_id>`: Fetch specific email
- POST `/emails`: Send new email
- PUT `/emails/<email_id>`: Update email status (read/archived)