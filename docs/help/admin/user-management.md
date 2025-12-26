# User Management

This guide covers everything you need to know about managing users in Thesis, from creating new accounts to exporting user data.

## Accessing User Management

Navigate to **Dashboard** → **Users** to open the **User Management** page.

The page subtitle reads "Manage all users and their access levels" and displays three summary cards:
- **Total Users** - Count of all registered users
- **Admin Users** - Number of administrators
- **Regular Users** - Number of standard users

## Viewing All Users

The user list displays in a table format with the following columns:
- **User** - Display name
- **Email** - User's email address
- **Role** - Either **Admin** or **User**
- **Created** - Account creation date
- **Actions** - Available operations

### Searching Users

Use the search field with placeholder text "Search users by name or email..." to filter the list.

### Filtering by Role

1. Locate the **Role:** dropdown
2. Select from:
   - **All Roles** - Shows everyone
   - **Admin** - Shows only administrators
   - **User** - Shows only standard users

### Sorting Users

1. Use the **Sort By:** dropdown to select:
   - **Date Created**
   - **Name**
   - **Email**

2. Use the **Order:** dropdown to choose:
   - **Descending**
   - **Ascending**

### Clearing Filters

Click **Clear Filters** to reset all search and filter criteria.

## Creating New Users

### Step-by-Step Process

1. Navigate to **Dashboard** → **Users**
2. Click the **+ Add User** button
3. The **Add New User** form appears with three fields:
   - **Email** - Enter the user's email address
   - **Name** - Enter the user's display name
   - **Role** - Select from dropdown:
     - **User** - Standard access
     - **Admin** - Administrative access
4. Click **Create User**
5. An invitation email is automatically sent to the new user

### Canceling User Creation

If you've opened the form but decide not to create a user:
- Click **Cancel** (the button that replaced **+ Add User**)
- The form will close

## Understanding User Roles

### Admin Role

Administrators can:
- Access the admin dashboard and all admin pages
- Manage other users (create, view details)
- View all documents and conversations
- Customize themes and branding
- Configure AI system instructions
- View all KPIs and analytics

### User Role

Standard users can:
- Access the chat interface
- Upload and manage their own documents
- View their conversation history
- Access projects and impact dashboard

## Resending Invitation Emails

If a user didn't receive their invitation or it expired:

1. Navigate to **Dashboard** → **Users**
2. Find the user in the table
3. In the **Actions** column, click **Resend Invitation** (actions are separated by a vertical bar: "View Details | Resend Invitation")
4. A new invitation email will be sent

## Viewing User Details

### Opening User Details

1. Navigate to **Dashboard** → **Users**
2. Find the user in the table
3. In the **Actions** column, click **View Details** (actions are separated by a vertical bar: "View Details | Resend Invitation")

### User Detail Tabs

The user detail page has three tabs:

#### Overview Tab

Displays the **User Information** section with:
- **Email** - User's email address
- **Role** - Admin or User
- **User ID** - Unique identifier
- **Client ID** - Associated client identifier
- **Created** - Account creation timestamp

Also shows the **Core Document Mappings** section with a link to configure AI instruction documents.

#### Prompts Tab

Shows **Quick Prompt Templates** - pre-configured prompts that appear in the user's chat sidebar for quick access to common tasks.

##### What Are Quick Prompts?

Quick Prompts are pre-written message templates that users can click to instantly send to Thesis. They appear in the user's chat sidebar and help users:
- Start common workflows quickly
- Use consistent phrasing for recurring tasks
- Access specialized features without remembering exact commands

##### Prompt Display

Each prompt card shows:
- **Title** - The prompt name displayed to the user
- **Auto-generated badge** - Teal badge indicating the prompt was created automatically based on user patterns or document analysis
- **Category** - Classification like "analysis", "writing", "planning"
- **Prompt Text** - The actual message that gets sent when clicked
- **Function** - The underlying capability the prompt activates (e.g., "document_analysis", "brainstorming")

##### Auto-Generated vs Manual Prompts

**Auto-generated prompts** are created by the system based on:
- User's uploaded documents and their content
- Common interaction patterns
- Mapped core documents and their frameworks

These prompts are marked with a teal **Auto-generated** badge and may include metadata about when they were generated and what function they serve.

**Manual prompts** (if available) are explicitly configured for the user and don't have the auto-generated badge.

##### Empty State

If no prompts exist, you'll see: "No prompts configured yet" with a message explaining that prompts can be added to help users quickly access common tasks.

##### Using Prompt Information

Review user prompts to:
- Understand what quick actions are available to the user
- Verify prompts align with their role and responsibilities
- Identify if auto-generation is working based on their documents
- Troubleshoot if users report missing or incorrect prompts

#### Chat History Tab

Provides the **Chat History Export** section:
- Description: "Download all chat messages for this user in JSON format"
- Button: **Export Chat History (JSON)**
- Shows "Exporting..." while processing

## Managing Core Documents for Users

Each user can have documents mapped to AI instruction template slots.

### Accessing Core Document Mappings

1. Navigate to **Dashboard** → **Users**
2. Click **View Details** for the user
3. In the **Overview** tab, find **Core Document Mappings**
4. Click **Manage Core Documents**

This opens the **Link Reference Documents** page where you can map documents to template slots.

See the Core Documents Mapping guide for detailed instructions.

## Best Practices for User Onboarding

### Before Creating the Account

1. Confirm the correct email address
2. Decide on the appropriate role (most users should be **User** role)
3. Ensure any necessary documents are uploaded

### Creating the Account

1. Use a professional email address
2. Enter the full name for easy identification
3. Double-check role selection before clicking **Create User**

### After Account Creation

1. Notify the user to check their email (including spam folder)
2. If using **Admin** role, explain their elevated permissions
3. Provide any necessary onboarding documentation

### If Invitation Doesn't Arrive

1. Wait a few minutes and check spam/junk folders
2. Click **Resend Invitation** from the user list
3. Verify the email address is correct

## Exporting User Data

### Exporting Chat History

To export a specific user's conversation history:

1. Navigate to **Dashboard** → **Users**
2. Click **View Details** for the user
3. Go to the **Chat History** tab
4. Click **Export Chat History (JSON)**
5. A JSON file downloads with all conversations and messages

The export includes:
- All conversation threads
- Individual messages with timestamps
- Message roles (user vs assistant)
- Conversation metadata

## Common User Management Tasks

### Adding a New Team Member

1. **Dashboard** → **Users** → **+ Add User**
2. Enter **Email**, **Name**, select **User** role
3. Click **Create User**

### Promoting a User to Admin

Currently, role changes require creating a new account with the desired role.

### Checking User Activity

1. View user's **Chat History** tab for conversation data
2. Check **Prompts** tab for configured quick prompts
3. Review **Core Document Mappings** for AI configuration

### Troubleshooting Login Issues

1. Verify the user exists in **Dashboard** → **Users**
2. Click **Resend Invitation** if they need a new login link
3. Confirm email address is correct
