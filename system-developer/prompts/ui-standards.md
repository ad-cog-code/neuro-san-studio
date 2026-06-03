# UI Design Standards — AppMagic Generated Apps
> Embedded in frontend_developer prompt. Every generated app MUST follow these standards.

---

## 1. Theme Selection

Choose theme based on the primary user of the app:

| Primary User | Theme | Rationale |
|---|---|---|
| Internal staff, admins, adjusters, analysts | **Dark** | Reduces eye strain in long sessions |
| Customers, patients, citizens, consumers | **Light** | More approachable, trust-building |
| Mixed (staff portal + customer portal) | **Dark** for staff routes, **Light** for customer routes |

---

## 2. Dark Theme — Exact Color Tokens

Use these exact hex values. Do not invent new greys.

```css
/* Dark Theme Color Tokens */
--bg-page:        #0f1117;   /* Page background */
--bg-surface:     #1a1d2e;   /* Cards, modals, panels */
--bg-sidebar:     #12141f;   /* Nav / sidebar */
--bg-input:       #12141f;   /* Form inputs */
--bg-hover:       rgba(108, 99, 255, 0.12);  /* Row hover, menu hover */

--border-subtle:  rgba(255, 255, 255, 0.08); /* Card borders, dividers */
--border-input:   rgba(255, 255, 255, 0.15); /* Input borders */
--border-focus:   #6c63ff;                   /* Focused input border */

--text-primary:   #e2e8f0;   /* Body text, headings */
--text-secondary: #94a3b8;   /* Labels, captions, placeholders */
--text-tertiary:  #64748b;   /* Very subdued, timestamps */
--text-inverse:   #ffffff;   /* Text on brand/accent backgrounds */

--brand:          #6c63ff;   /* Primary accent / CTA */
--brand-hover:    #5a52e0;   /* Brand on hover */
--brand-subtle:   rgba(108, 99, 255, 0.15); /* Light tint backgrounds */

--success:        #10b981;
--warning:        #f59e0b;
--danger:         #ef4444;
--info:           #3b82f6;

--success-subtle: rgba(16, 185, 129, 0.12);
--warning-subtle: rgba(245, 158, 11, 0.12);
--danger-subtle:  rgba(239, 68, 68, 0.12);
--info-subtle:    rgba(59, 130, 246, 0.12);
```

---

## 3. Light Theme — Exact Color Tokens

```css
/* Light Theme Color Tokens */
--bg-page:        #f8fafc;
--bg-surface:     #ffffff;
--bg-sidebar:     #1e293b;   /* Dark sidebar on light page */
--bg-input:       #ffffff;
--bg-hover:       rgba(108, 99, 255, 0.06);

--border-subtle:  #e2e8f0;
--border-input:   #cbd5e1;
--border-focus:   #6c63ff;

--text-primary:   #1e293b;
--text-secondary: #64748b;
--text-tertiary:  #94a3b8;
--text-inverse:   #ffffff;   /* Text in dark sidebar */

--brand:          #6c63ff;
--brand-hover:    #5a52e0;
--brand-subtle:   rgba(108, 99, 255, 0.08);

--success:        #059669;
--warning:        #d97706;
--danger:         #dc2626;
--info:           #2563eb;
```

---

## 4. Typography

### Font Stack
Always load Inter from Google Fonts. Place in `<head>` of `base.html`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

Apply globally in `style.css`:
```css
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  background-color: var(--bg-page);
}
```

### Type Scale
| Element | Size | Weight | Color |
|---|---|---|---|
| Page title (h1) | 24px | 700 | text-primary |
| Section heading (h2) | 20px | 600 | text-primary |
| Card title (h5/h6) | 16px | 600 | text-primary |
| Body text | 14px | 400 | text-primary |
| Form labels | 13px | 500 | text-secondary |
| Small / captions | 12px | 400 | text-secondary |
| Badges | 11px | 600 | depends on variant |

### Contrast Rule (WCAG AA minimum)
- Body text on dark background: minimum 4.5:1 ratio → use `#e2e8f0` on `#0f1117` ✓
- Secondary text: minimum 3:1 → use `#94a3b8` on `#0f1117` ✓
- Never use Bootstrap's default dark text (`#212529`) on dark backgrounds — always override

---

## 5. Bootstrap 5 Mandatory Overrides (Dark Theme)

Copy this block into every dark-theme app's `style.css`. These MUST come AFTER the Bootstrap CDN link in base.html.

```css
/* ── Bootstrap 5 Dark Overrides — MANDATORY ─────────────── */
body          { color: var(--text-primary); background-color: var(--bg-page); }
h1,h2,h3,h4,h5,h6 { color: var(--text-primary); }
p, span, div, label, small, li { color: inherit; }
.text-muted   { color: var(--text-secondary) !important; }

/* Tables */
.table        { color: var(--text-primary); }
.table > :not(caption) > * > * { color: var(--text-primary); background-color: transparent; }
.table-striped > tbody > tr:nth-of-type(odd) > * { background-color: rgba(255,255,255,0.03); }
.table-hover > tbody > tr:hover > * { background-color: var(--bg-hover); }
.table thead th { color: var(--text-secondary); font-size: 11px; font-weight: 600;
                  text-transform: uppercase; letter-spacing: 0.05em; border-bottom-color: var(--border-subtle); }

/* Cards */
.card         { background-color: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 10px; }
.card-header  { background-color: transparent; border-bottom: 1px solid var(--border-subtle);
                font-weight: 600; color: var(--text-primary); }
.card-body    { background-color: transparent; }
.card-footer  { background-color: transparent; border-top: 1px solid var(--border-subtle); }

/* Forms */
.form-control, .form-select {
  background-color: var(--bg-input);
  border: 1px solid var(--border-input);
  color: var(--text-primary);
  border-radius: 6px;
}
.form-control:focus, .form-select:focus {
  background-color: var(--bg-input);
  border-color: var(--border-focus);
  color: var(--text-primary);
  box-shadow: 0 0 0 3px rgba(108,99,255,0.2);
}
.form-control::placeholder { color: var(--text-tertiary); }
.form-label   { color: var(--text-secondary); font-size: 13px; font-weight: 500; margin-bottom: 4px; }
.form-text    { color: var(--text-tertiary); font-size: 12px; }
.input-group-text { background-color: var(--bg-input); border-color: var(--border-input); color: var(--text-secondary); }

/* Navigation */
.navbar       { background-color: var(--bg-sidebar) !important; border-bottom: 1px solid var(--border-subtle); }
.navbar-brand { color: var(--text-primary) !important; font-weight: 700; font-size: 16px; }
.nav-link     { color: var(--text-secondary) !important; font-size: 14px; }
.nav-link:hover, .nav-link.active { color: var(--text-primary) !important; }

/* Buttons */
.btn-primary  { background-color: var(--brand); border-color: var(--brand); color: #fff; }
.btn-primary:hover { background-color: var(--brand-hover); border-color: var(--brand-hover); }
.btn-outline-primary { color: var(--brand); border-color: var(--brand); }
.btn-outline-primary:hover { background-color: var(--brand); color: #fff; }
.btn          { border-radius: 6px; font-size: 14px; font-weight: 500; }
.btn-sm       { font-size: 12px; }

/* Modals */
.modal-content { background-color: var(--bg-surface); border: 1px solid var(--border-subtle); }
.modal-header  { border-bottom-color: var(--border-subtle); }
.modal-footer  { border-top-color: var(--border-subtle); }
.modal-title   { color: var(--text-primary); font-weight: 600; }

/* Dropdowns */
.dropdown-menu { background-color: var(--bg-surface); border: 1px solid var(--border-subtle); }
.dropdown-item { color: var(--text-primary); font-size: 14px; }
.dropdown-item:hover { background-color: var(--bg-hover); color: var(--text-primary); }
.dropdown-divider { border-color: var(--border-subtle); }
.dropdown-header { color: var(--text-secondary); font-size: 11px; font-weight: 600;
                   text-transform: uppercase; letter-spacing: 0.05em; }

/* List groups */
.list-group-item { background-color: var(--bg-surface); border-color: var(--border-subtle); color: var(--text-primary); }
.list-group-item:hover { background-color: var(--bg-hover); }
.list-group-item.active { background-color: var(--brand); border-color: var(--brand); }

/* Badges */
.badge { font-weight: 600; border-radius: 4px; font-size: 11px; padding: 3px 8px; }

/* Alerts */
.alert { border-radius: 8px; border: none; }
.alert-success { background-color: var(--success-subtle); color: var(--success); }
.alert-warning { background-color: var(--warning-subtle); color: var(--warning); }
.alert-danger  { background-color: var(--danger-subtle); color: var(--danger); }
.alert-info    { background-color: var(--info-subtle); color: var(--info); }

/* Breadcrumbs, HR, borders */
.breadcrumb-item, .breadcrumb-item a { color: var(--text-secondary); font-size: 13px; }
.breadcrumb-item.active { color: var(--text-primary); }
hr { border-color: var(--border-subtle); opacity: 1; }
.border        { border-color: var(--border-subtle) !important; }
.border-top    { border-top-color: var(--border-subtle) !important; }
.border-bottom { border-bottom-color: var(--border-subtle) !important; }
.bg-light { background-color: var(--bg-surface) !important; }

/* Code */
code { color: #f472b6; background-color: rgba(244,114,182,0.1); padding: 1px 5px; border-radius: 3px; }
pre  { background-color: #0d0f1a; border: 1px solid var(--border-subtle); border-radius: 6px; padding: 12px; color: #e2e8f0; }
```

---

## 6. Bootstrap 5 Mandatory Overrides (Light Theme)

```css
/* ── Bootstrap 5 Light Overrides — MANDATORY ────────────── */
body          { color: var(--text-primary); background-color: var(--bg-page); font-family: 'Inter', sans-serif; }
h1,h2,h3,h4,h5,h6 { color: var(--text-primary); }
.text-muted   { color: var(--text-secondary) !important; }

.card         { border: 1px solid var(--border-subtle); border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.card-header  { background-color: var(--bg-page); border-bottom: 1px solid var(--border-subtle); font-weight: 600; }

.form-control, .form-select { border-color: var(--border-input); border-radius: 6px; }
.form-control:focus, .form-select:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(108,99,255,0.15);
}
.form-label   { color: var(--text-secondary); font-size: 13px; font-weight: 500; }

/* Dark sidebar on light theme */
.sidebar      { background-color: var(--bg-sidebar); }
.sidebar .nav-link { color: rgba(255,255,255,0.7); }
.sidebar .nav-link:hover, .sidebar .nav-link.active { color: #fff; background-color: rgba(255,255,255,0.1); }
.sidebar .navbar-brand { color: #fff; }

.btn-primary  { background-color: var(--brand); border-color: var(--brand); }
.btn-primary:hover { background-color: var(--brand-hover); border-color: var(--brand-hover); }
.table thead th { color: var(--text-secondary); font-size: 11px; font-weight: 600;
                  text-transform: uppercase; letter-spacing: 0.05em; }
```

---

## 7. Component Patterns

### 7.1 base.html Structure
Every generated app's `base.html` must include:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}App Name{% endblock %}</title>
  <!-- Google Fonts: Inter -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <!-- Bootstrap 5 CDN -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <!-- Bootstrap Icons CDN -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
  <!-- App CSS (overrides must come AFTER Bootstrap) -->
  <link href="{{ url_for('static', filename='style.css') }}" rel="stylesheet">
  {% block head %}{% endblock %}
</head>
<body>
  <!-- Navbar -->
  <nav class="navbar navbar-expand-lg sticky-top">
    <div class="container-fluid px-4">
      <a class="navbar-brand d-flex align-items-center gap-2" href="{{ url_for('main.index') }}">
        <i class="bi bi-[app-icon]"></i> App Name
      </a>
      <div class="navbar-nav ms-auto d-flex flex-row gap-2 align-items-center">
        {% if session.get('user_id') %}
        <span class="text-secondary small">{{ session.get('username', '') }}</span>
        <a href="{{ url_for('auth.logout') }}" class="btn btn-sm btn-outline-secondary">Logout</a>
        {% endif %}
      </div>
    </div>
  </nav>

  <!-- Flash messages -->
  <div class="container-fluid px-4 mt-3">
    {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      {% for cat, msg in messages %}
      <div class="alert alert-{{ 'danger' if cat == 'error' else cat }} alert-dismissible fade show" role="alert">
        <i class="bi bi-{{ 'exclamation-triangle' if cat in ('error','danger','warning') else 'check-circle' }}-fill me-2"></i>
        {{ msg }}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
      {% endfor %}
    {% endif %}
    {% endwith %}
  </div>

  <!-- Main content -->
  <main class="container-fluid px-4 py-4">
    {% block content %}{% endblock %}
  </main>

  <!-- Scripts -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  {% block scripts %}{% endblock %}
</body>
</html>
```

### 7.2 Page Header Pattern
Every page template must open with a page header row:
```html
{% block content %}
<div class="d-flex align-items-center justify-content-between mb-4">
  <div>
    <h1 class="mb-1" style="font-size:22px;font-weight:700;">Page Title</h1>
    <p class="text-muted mb-0" style="font-size:13px;">Brief description of this page</p>
  </div>
  <div class="d-flex gap-2">
    <!-- Primary action button here -->
    <button class="btn btn-primary btn-sm">
      <i class="bi bi-plus-lg me-1"></i> Primary Action
    </button>
  </div>
</div>
{% endblock %}
```

### 7.3 Data Table Pattern
```html
<div class="card">
  <div class="card-header d-flex align-items-center justify-content-between">
    <h6 class="mb-0">Table Title</h6>
    <span class="badge bg-secondary">{{ items|length }} records</span>
  </div>
  <div class="card-body p-0">
    <div class="table-responsive">
      <table class="table table-hover mb-0">
        <thead>
          <tr>
            <th>Column</th>
            <th>Column</th>
            <th style="width:100px;">Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for item in items %}
          <tr>
            <td>{{ item.name }}</td>
            <td><span class="text-muted small">{{ item.created_at }}</span></td>
            <td>
              <a href="{{ url_for('main.view', id=item.id) }}"
                 class="btn btn-sm btn-outline-primary py-0 px-2">View</a>
            </td>
          </tr>
          {% else %}
          <tr>
            <td colspan="3" class="text-center text-muted py-4">
              <i class="bi bi-inbox fs-4 d-block mb-2"></i>No records yet
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
```

### 7.4 Form Card Pattern
```html
<div class="row justify-content-center">
  <div class="col-lg-7">
    <div class="card">
      <div class="card-header">
        <h6 class="mb-0"><i class="bi bi-pencil-square me-2"></i>Form Title</h6>
      </div>
      <div class="card-body">
        <form method="POST" action="{{ url_for('main.save') }}">
          <div class="mb-3">
            <label class="form-label">Field Label <span class="text-danger">*</span></label>
            <input type="text" class="form-control" name="field" placeholder="Enter value" required>
            <div class="form-text">Helper text if needed</div>
          </div>
          <div class="mb-3">
            <label class="form-label">Status</label>
            <select class="form-select" name="status">
              <option value="">Select status...</option>
              <option value="active">Active</option>
            </select>
          </div>
          <div class="d-flex gap-2 mt-4">
            <button type="submit" class="btn btn-primary">
              <i class="bi bi-check-lg me-1"></i> Save
            </button>
            <a href="{{ url_for('main.list') }}" class="btn btn-outline-secondary">Cancel</a>
          </div>
        </form>
      </div>
    </div>
  </div>
</div>
```

### 7.5 Stat Cards / KPI Row
```html
<div class="row g-3 mb-4">
  <div class="col-md-3">
    <div class="card h-100">
      <div class="card-body">
        <div class="d-flex align-items-start justify-content-between">
          <div>
            <p class="text-muted small mb-1" style="font-size:12px;text-transform:uppercase;letter-spacing:.05em;">Total Claims</p>
            <h3 class="mb-0" style="font-size:28px;font-weight:700;">{{ total }}</h3>
            <p class="text-muted small mb-0 mt-1">+12% this month</p>
          </div>
          <div class="rounded-3 p-2" style="background:var(--brand-subtle);">
            <i class="bi bi-clipboard-data fs-4" style="color:var(--brand);"></i>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

### 7.6 Status Badge Pattern
```css
/* Status badges — always define these for domain-specific states */
.badge-status-pending   { background: var(--warning-subtle); color: var(--warning); }
.badge-status-active    { background: var(--success-subtle); color: var(--success); }
.badge-status-closed    { background: rgba(148,163,184,0.15); color: #94a3b8; }
.badge-status-rejected  { background: var(--danger-subtle); color: var(--danger); }
.badge-status-review    { background: var(--info-subtle); color: var(--info); }
```

Use in templates:
```html
<span class="badge badge-status-{{ item.status|lower }}">{{ item.status }}</span>
```

### 7.7 Sidebar Layout (for admin apps)
```html
<div class="d-flex" style="min-height:calc(100vh - 56px)">
  <!-- Sidebar -->
  <nav class="sidebar d-flex flex-column p-3" style="width:220px;min-width:220px;">
    <div class="nav flex-column gap-1">
      <a href="{{ url_for('main.dashboard') }}"
         class="nav-link rounded-2 px-3 py-2 {{ 'active' if request.endpoint == 'main.dashboard' else '' }}">
        <i class="bi bi-speedometer2 me-2"></i>Dashboard
      </a>
      <a href="{{ url_for('main.items') }}"
         class="nav-link rounded-2 px-3 py-2 {{ 'active' if 'items' in request.endpoint else '' }}">
        <i class="bi bi-list-ul me-2"></i>Items
      </a>
      <hr>
      <p class="px-3 mb-1" style="font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:rgba(255,255,255,0.35);">Admin</p>
      <a href="{{ url_for('admin.users') }}" class="nav-link rounded-2 px-3 py-2">
        <i class="bi bi-people me-2"></i>Users
      </a>
    </div>
  </nav>
  <!-- Main content -->
  <main class="flex-grow-1 p-4" style="overflow-x:hidden;">
    {% block content %}{% endblock %}
  </main>
</div>
```

---

## 8. Login Page Pattern

Login pages must be centred, minimal, professional:
```html
{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center align-items-center" style="min-height:80vh;">
  <div class="col-sm-10 col-md-6 col-lg-4">
    <div class="text-center mb-4">
      <i class="bi bi-[app-icon]" style="font-size:40px;color:var(--brand);"></i>
      <h2 class="mt-2 mb-1" style="font-size:22px;font-weight:700;">App Name</h2>
      <p class="text-muted small">Sign in to continue</p>
    </div>
    <div class="card">
      <div class="card-body p-4">
        <form method="POST">
          <div class="mb-3">
            <label class="form-label">Username</label>
            <input type="text" class="form-control" name="username" autofocus required>
          </div>
          <div class="mb-4">
            <label class="form-label">Password</label>
            <input type="password" class="form-control" name="password" required>
          </div>
          <button type="submit" class="btn btn-primary w-100">Sign In</button>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

---

## 9. Empty States

Every list page must handle the empty state gracefully:
```html
<!-- When no records exist -->
<div class="text-center py-5">
  <i class="bi bi-[relevant-icon]" style="font-size:48px;color:var(--text-tertiary);"></i>
  <h5 class="mt-3 mb-1" style="font-size:16px;color:var(--text-secondary);">No [items] yet</h5>
  <p class="text-muted small mb-3">Get started by creating your first [item]</p>
  <a href="{{ url_for('main.create') }}" class="btn btn-primary btn-sm">
    <i class="bi bi-plus-lg me-1"></i> Create [Item]
  </a>
</div>
```

---

## 10. Toast / Notification JavaScript
Include this in every app's `static/js/main.js`:
```javascript
function toast(message, type = 'success') {
  const colors = {
    success: 'var(--success)', error: 'var(--danger)',
    warning: 'var(--warning)', info: 'var(--info)'
  };
  const icons = {
    success: 'check-circle-fill', error: 'exclamation-triangle-fill',
    warning: 'exclamation-triangle-fill', info: 'info-circle-fill'
  };
  const el = document.createElement('div');
  el.className = 'position-fixed bottom-0 end-0 m-4 p-3 rounded-3 d-flex align-items-center gap-2';
  el.style.cssText = `background:var(--bg-surface);border:1px solid var(--border-subtle);
    box-shadow:0 8px 24px rgba(0,0,0,0.3);z-index:9999;min-width:260px;max-width:400px;`;
  el.innerHTML = `<i class="bi bi-${icons[type]}" style="color:${colors[type]};font-size:16px;flex-shrink:0;"></i>
    <span style="font-size:14px;">${message}</span>`;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}
```

---

## 11. Key Principles — Non-Negotiable

1. **Dark or light — decide once, apply everywhere.** Mixed themes on the same page look broken.
2. **CSS variables first.** Every color reference must use `var(--token)` not a raw hex. Raw hexes are maintenance debt.
3. **Bootstrap text defaults kill dark UIs.** The mandatory overrides section must be present and complete.
4. **Every interactive element has a hover/focus state.** No bare elements.
5. **Every list has an empty state.** No white voids.
6. **Icons are decorative context.** Use Bootstrap Icons for every button, nav link, and heading. `<i class="bi bi-X me-2"></i>` before labels.
7. **Consistent spacing.** Use Bootstrap spacing utilities (`mb-3`, `py-4`, `gap-2`) — never arbitrary `margin: 7px`.
8. **Mobile-responsive by default.** Use Bootstrap grid (`col-lg-8 col-md-12`) and `table-responsive` wrapper.
9. **Forms have labels, placeholders, and helper text.** No unlabelled inputs.
10. **Buttons have a primary hierarchy.** One primary CTA per page section; secondary/outline for cancel/back.
