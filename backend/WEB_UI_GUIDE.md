# Web UI Guide - DNS Management System

## Overview

A complete web-based dashboard for managing DNS records with role-based access control:
- **Admin users**: Can read and write (add, edit, delete records)
- **Normal users**: Can only read (view records and query DNS)

## Features

### ✅ Implemented Features

1. **User Authentication**
   - Login/Logout functionality
   - Session-based authentication
   - Role-based access control

2. **Dashboard**
   - Statistics overview (total, manual, cached records)
   - Recent records display
   - Quick action buttons

3. **DNS Query Interface**
   - Query any domain name
   - Support for all record types (A, AAAA, CNAME, MX, TXT, PTR, NS)
   - Real-time DNS resolution
   - Results displayed in a user-friendly format

4. **Records Management**
   - View all DNS records (manual and cached)
   - Search and filter functionality
   - Separate views for manual vs cached records
   - **Admin only**: Add, Edit, Delete records

5. **Modern UI**
   - Responsive design
   - Clean, modern interface
   - Gradient color scheme
   - User-friendly forms and tables

## Setup Instructions

### 1. Create Users

First, create users with different roles:

```bash
cd backend
python manage.py createsuperuser
```

This creates an **admin user** (can read and write).

To create a **normal user** (read-only):
1. Go to Django admin: `http://localhost:8000/admin/`
2. Login with admin credentials
3. Go to "Users" → "Add user"
4. Create a user (uncheck "Staff status" for normal user)
5. Set a password

### 2. Start the Server

```bash
cd backend
python manage.py runserver
```

### 3. Access the Web UI

Open your browser and go to:
- **Main Dashboard**: `http://localhost:8000/`
- **Login Page**: `http://localhost:8000/login/`

## Usage Guide

### For Normal Users (Read-Only)

1. **Login**: Go to `/login/` and enter your credentials
2. **Dashboard**: View statistics and recent records
3. **Query DNS**: 
   - Go to "Query DNS" in the navbar
   - Enter a domain name (e.g., `google.com`)
   - Select record type (A, AAAA, etc.)
   - Click "Query" to see results
4. **View Records**: 
   - Go to "Records" in the navbar
   - Browse all DNS records
   - Use search and filter options
   - **Note**: You cannot add, edit, or delete records

### For Admin Users (Read/Write)

1. **Login**: Go to `/login/` and enter admin credentials
2. **All Normal User Features**: Everything above, plus:
3. **Add Records**:
   - Click "Add Record" in the navbar
   - Fill in the form:
     - Domain (must end with `.`)
     - Record Type (A, AAAA, CNAME, MX, etc.)
     - Value (IP address or domain)
     - TTL (Time To Live in seconds)
     - Priority (for MX records)
   - Click "Add Record"
4. **Edit Records**:
   - Go to "Records"
   - Click "Edit" next to any manual record
   - Modify the fields
   - Click "Update Record"
5. **Delete Records**:
   - Go to "Records"
   - Click "Delete" next to any record
   - Confirm deletion

## URL Routes

### Web UI Routes
- `/` - Dashboard (requires login)
- `/login/` - Login page
- `/logout/` - Logout (redirects to login)
- `/query/` - DNS Query interface (requires login)
- `/records/` - Records list (requires login)
- `/records/add/` - Add record (admin only)
- `/records/<id>/edit/` - Edit record (admin only)
- `/records/<id>/delete/` - Delete record (admin only)

### API Routes (unchanged)
- `/api/v1/dns-query` - DoH endpoint
- `/api/v1/admin/record` - Add record (API)
- `/api/v1/admin/records` - List records (API)
- `/api/v1/admin/record/<domain>` - Delete record (API)

## User Roles

### Admin User (`is_staff=True`)
- ✅ View dashboard
- ✅ Query DNS
- ✅ View all records
- ✅ Add records
- ✅ Edit records
- ✅ Delete records
- ✅ Access Django admin panel

### Normal User (`is_staff=False`)
- ✅ View dashboard
- ✅ Query DNS
- ✅ View all records
- ❌ Add records (redirected or shown error)
- ❌ Edit records (no edit button shown)
- ❌ Delete records (no delete button shown)
- ❌ Access Django admin panel

## Security Features

1. **Authentication Required**: All pages except login require authentication
2. **Role-Based Access**: Admin-only actions are protected with `@user_passes_test(is_admin)`
3. **CSRF Protection**: All forms include CSRF tokens
4. **Session Management**: Secure session handling via Django

## Troubleshooting

### "You don't have permission to access this page"
- Make sure you're logged in
- For admin-only pages, ensure your user has `is_staff=True`
- Check in Django admin: `/admin/auth/user/`

### "Login page keeps redirecting"
- Clear browser cookies
- Make sure you're using the correct credentials
- Check that the user account is active

### "Can't see Add/Edit/Delete buttons"
- You're logged in as a normal user
- Create an admin user or ask an admin to grant you staff status

## Next Steps

The web UI is fully functional! You can now:
1. Create users with different roles
2. Test the dashboard and query features
3. Manage DNS records through the web interface
4. Use the API endpoints for programmatic access

Enjoy your DNS Management System! 🎉

