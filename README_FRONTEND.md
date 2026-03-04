# 📋 FRONTEND PLAN (React + TypeScript) — README_FRONTEND.md

## Project Overview
CloudIaaS frontend — web dashboard for managing virtual machines, networks, quotas and users.
Consumes the FastAPI backend REST API.

> ⚠️ No existing frontend found in this repo. This plan starts from scratch.

## Tech Stack
- React 18 + TypeScript 5
- Vite 5
- TanStack Query v5 (React Query) — server state
- React Router v6 (createBrowserRouter)
- Zustand — client/auth state
- Axios — HTTP client
- Tailwind CSS + shadcn/ui — components
- React Hook Form + Zod — forms & validation
- Vitest + React Testing Library + MSW — tests

## Team
- **Dev-1**: Project Lead / Architecture & Routing
- **Dev-2**: UI Components & Design System
- **Dev-3**: State Management & API Integration
- **Dev-4**: Forms, CRUD Pages & User Flows
- **Dev-5**: Testing, CI & Build Optimization

## Backend API Base URL
`http://localhost:8000` (dev) — configure via `VITE_API_URL` env variable.

---

## DAY 1 — Project Scaffold & Foundation

### 1.1 [Dev-1] Project Scaffold & Router
- [ ] Initialize Vite + React + TS project with routing

<details>
<summary>📎 Copilot Prompt</summary>

```
Create a new React 18 + TypeScript + Vite project (npm create vite@latest frontend -- --template react-ts).
Set up the following folder structure under src/:
  src/api/          ← axios client, endpoint functions, types
  src/components/ui/     ← base reusable components
  src/components/features/  ← domain-specific components
  src/pages/        ← full page components
  src/hooks/        ← custom React Query hooks
  src/store/        ← Zustand stores
  src/types/        ← shared TypeScript interfaces
  src/lib/          ← zod schemas, utils
  src/router/       ← React Router config
  src/tests/        ← test files

In src/main.tsx:
- Wrap app in <QueryClientProvider client={queryClient}> (TanStack Query v5)
- Wrap in <RouterProvider router={router}>
- Add global ErrorBoundary wrapper

In src/router/index.tsx use createBrowserRouter with:
  / → redirect to /dashboard
  /login → LoginPage (public)
  /register → RegisterPage (public)
  /register/confirm → ConfirmEmailPage (public)
  /dashboard → DashboardPage (protected, lazy)
  /vms → VMListPage (protected, lazy)
  /vms/:id → VMDetailPage (protected, lazy)
  /networks → NetworkListPage (protected, lazy)
  /users → UserListPage (protected, admin only, lazy)
  /profile → ProfilePage (protected, lazy)
  * → NotFoundPage

All protected routes wrapped in <ProtectedRoute> component.
```
</details>

---

### 1.2 [Dev-2] Design System & Base Components
- [ ] Set up Tailwind + shadcn/ui and create base components

<details>
<summary>📎 Copilot Prompt</summary>

```
In the React + TypeScript + Vite project:
1. Install and configure Tailwind CSS v3 with postcss.
2. Install shadcn/ui: npx shadcn-ui@latest init (use slate color, CSS variables).
3. Add shadcn components: button, input, label, card, badge, dialog, dropdown-menu, table, toast, avatar, skeleton, separator.

Create src/components/ui/PageLayout.tsx:
  - props: title: string, actions?: ReactNode, children: ReactNode
  - renders a page wrapper with heading and optional action buttons (e.g. "Create VM")

Create src/components/ui/DataTable.tsx:
  - generic typed component: DataTable<T>
  - props: columns: ColumnDef<T>[], data: T[], isLoading: boolean, pagination: {page, total, pageSize, onPageChange}
  - shows Skeleton rows when isLoading
  - shows EmptyState component when data is empty

Create src/components/ui/EmptyState.tsx:
  - props: title, description, action?: ReactNode
  - centered illustration + text + optional button

Create src/components/ui/ConfirmDialog.tsx:
  - props: open, onConfirm, onCancel, title, description, confirmLabel, isLoading
  - uses shadcn Dialog, shows spinner on confirmLabel button when isLoading
```
</details>

---

### 1.3 [Dev-3] API Client + TypeScript types
- [ ] Create Axios client and all API type definitions

<details>
<summary>📎 Copilot Prompt</summary>

```
Read the FastAPI backend API endpoints:
  POST /auth/register, POST /auth/token (OAuth2 form), POST /auth/refresh,
  GET /auth/me, PATCH /auth/change_password,
  GET /users, GET /users/{id}, PATCH /users/{id}, DELETE /users/delete,
  GET /vms, POST /vms, GET /vms/{id}, PATCH /vms/{id}, DELETE /vms/{id},
  GET /networks, POST /networks, GET /networks/{id}, PATCH /networks/{id}, DELETE /networks/{id},
  POST /networks/{id}/attach-vm, POST /networks/{id}/detach-vm,
  GET /health

Create src/api/client.ts:
- axios instance with baseURL from import.meta.env.VITE_API_URL
- request interceptor: attach Authorization: Bearer {token} from localStorage key "access_token"
- response interceptor: on 401 → clear tokens, redirect to /login; on any error → throw structured ApiError

Create src/api/types.ts with TypeScript interfaces matching backend Pydantic schemas:
  User, UserUpdate, CreateUser, Tokens, RefreshToken, ChangePassword
  VirtualMachine (id, owner_id, name, status: 'pending'|'running'|'stopped'|'error', cpu_cores, ram_mb, disk_gb, ip_address, created_at)
  VMCreate, VMUpdate
  Network, NetworkCreate, NetworkUpdate
  Quota
  PaginatedResponse<T> { items: T[]; total: number; page: number; pages: number }
  ApiError { detail: string; status: number }

Create src/api/auth.ts, src/api/users.ts, src/api/vms.ts, src/api/networks.ts
with typed async functions wrapping axios calls for each endpoint.
```
</details>

---

### 1.4 [Dev-4] Auth Pages + Zustand Store
- [ ] Implement login, register pages and auth state

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/api/auth.ts and src/api/types.ts.

Create src/store/authStore.ts with Zustand:
  state: { user: User | null; accessToken: string | null; refreshToken: string | null; isAuthenticated: boolean }
  actions:
    login(tokens: Tokens, user: User) → stores tokens in localStorage + state
    logout() → clears localStorage + state, redirects to /login
    setUser(user: User) → updates user in state
  Persist tokens to localStorage using zustand/middleware persist.

Create src/pages/LoginPage.tsx:
  - React Hook Form with Zod schema: { username: z.string().min(1), password: z.string().min(1) }
  - Calls POST /auth/token (OAuth2 form: username/password as FormData)
  - On success: calls authStore.login(), navigate to /dashboard
  - Shows inline field errors and a toast on API error
  - Link to /register

Create src/pages/RegisterPage.tsx:
  - Fields: email, username, password, confirmPassword (Zod: passwords must match)
  - Calls POST /auth/register
  - On success: show "Check your email to confirm registration" message
  - Link to /login

Create src/pages/ConfirmEmailPage.tsx:
  - Reads ?token= from URL query params
  - Calls GET /auth/register_confirm?token=...
  - Shows success or error message

Create src/components/ProtectedRoute.tsx:
  - Reads isAuthenticated from authStore
  - If false: <Navigate to="/login" replace />
  - If role check needed (adminOnly prop): check user.role === 'admin', else redirect to /dashboard
```
</details>

---

### 1.5 [Dev-5] App Layout + Navigation
- [ ] Build main app shell with sidebar

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/store/authStore.ts and src/router/index.tsx.

Create src/components/layout/Sidebar.tsx:
  - Navigation links: Dashboard (/dashboard), Virtual Machines (/vms), Networks (/networks), Profile (/profile)
  - Admin-only link: Users (/users) — show only if authStore user.role === 'admin'
  - Active link highlighted using NavLink from react-router-dom
  - Collapsible on mobile (toggle button)
  - Bottom section: user avatar + username + logout button (calls authStore.logout())

Create src/components/layout/Topbar.tsx:
  - Shows current page title (from a usePageTitle hook)
  - Shows user avatar (initials if no avatar_url) + dropdown: "Profile", "Logout"
  - Mobile: hamburger button to toggle sidebar

Create src/components/layout/AppLayout.tsx:
  - Combines Sidebar + Topbar + <Outlet /> (React Router nested layout)
  - Responsive: sidebar hidden on mobile, overlay drawer

Create src/pages/DashboardPage.tsx:
  - Stats cards: Total VMs, Running VMs, Total Networks, My Profile (user info)
  - Each card uses shadcn Card component with an icon and count
  - Data fetched via GET /health (just to show connectivity) and counts from VMs/Networks lists

Update src/router/index.tsx to use AppLayout as the layout route for all protected pages.
```
</details>

---

## DAY 2 — Feature Pages & CRUD

### 2.1 [Dev-3] React Query Hooks
- [ ] Create all TanStack Query hooks for every entity

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/api/vms.ts, src/api/networks.ts, src/api/users.ts, src/api/types.ts.

Create src/api/queryKeys.ts exporting const queryKeys object:
  vms: { all, list(params), detail(id) }
  networks: { all, list(params), detail(id) }
  users: { all, list(params), detail(id) }
  auth: { me }

Create src/hooks/useVMs.ts with TanStack Query v5 hooks:
  useVMList(params: {page, pageSize}) → useQuery returning PaginatedResponse<VirtualMachine>
  useVM(id: string) → useQuery returning VirtualMachine
  useCreateVM() → useMutation, on success invalidates queryKeys.vms.all
  useUpdateVM() → useMutation(({id, data}) => ...), on success invalidates detail + list
  useDeleteVM() → useMutation(id => ...), on success invalidates queryKeys.vms.all
  Each mutation shows a toast on success and on error.

Create src/hooks/useNetworks.ts with equivalent hooks for Network entity.

Create src/hooks/useUsers.ts with equivalent hooks for User entity.

Create src/hooks/useAuth.ts:
  useMe() → useQuery GET /auth/me, populates authStore.setUser on success
  useChangePassword() → useMutation PATCH /auth/change_password
```
</details>

---

### 2.2 [Dev-2] VM Feature Components
- [ ] Build VM list, card and status components

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/types/ (VirtualMachine interface) and src/components/ui/DataTable.tsx.

Create src/components/features/vms/VMStatusBadge.tsx:
  - Props: status: 'pending'|'running'|'stopped'|'error'
  - Uses shadcn Badge with color variants: pending=yellow, running=green, stopped=gray, error=red
  - Shows a colored dot + status text

Create src/components/features/vms/VMTable.tsx:
  - Uses DataTable<VirtualMachine>
  - Columns: Name, Status (VMStatusBadge), CPU, RAM (format MB→GB), Disk (GB), IP, Created At, Actions
  - Actions column: Edit button (pencil icon), Delete button (trash icon, triggers ConfirmDialog)
  - Row click navigates to /vms/{id}

Create src/components/features/vms/VMStats.tsx:
  - Props: vms: VirtualMachine[]
  - Shows 3 mini-cards: Total, Running, Stopped counts

Create src/components/features/vms/VMSkeleton.tsx:
  - 5 rows of Skeleton components matching VMTable column widths
```
</details>

---

### 2.3 [Dev-4] VM Form + Create/Edit Pages
- [ ] Build VM create/edit form with validation

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/api/types.ts (VMCreate, VMUpdate) and src/hooks/useVMs.ts.

Create src/lib/schemas/vm.schema.ts with Zod:
  vmCreateSchema: { name: z.string().min(3).max(100), cpu_cores: z.number().int().min(1).max(64), ram_mb: z.number().int().min(512).max(131072), disk_gb: z.number().int().min(10).max(2000) }
  vmUpdateSchema: all fields optional

Create src/components/features/vms/VMForm.tsx:
  - Props: defaultValues?: Partial<VMCreate>, onSubmit(data): void, isLoading: boolean, mode: 'create'|'edit'
  - React Hook Form + zodResolver(vmCreateSchema)
  - Fields: Name (text input), CPU Cores (number, stepper), RAM MB (number with helper "512 MB = 0.5 GB"), Disk GB (number)
  - Submit button shows spinner when isLoading

Create src/pages/VMCreatePage.tsx:
  - Uses useCreateVM() mutation
  - On success: navigate to /vms/{newVM.id} + show success toast

Create src/pages/VMEditPage.tsx:
  - Uses useVM(id) to pre-fill form
  - Uses useUpdateVM() mutation
  - On success: navigate back to /vms/{id}

Create src/pages/VMDetailPage.tsx:
  - Shows VM info card (all fields), VMStatusBadge, owner info
  - Edit button → navigate to /vms/{id}/edit
  - Delete button → ConfirmDialog → useDeleteVM() → navigate to /vms

Create src/pages/VMListPage.tsx:
  - PageLayout title="Virtual Machines" actions={<CreateButton />}
  - VMStats at top
  - VMTable with pagination state (useState for page/pageSize)
  - Search input (debounced 300ms, filters by name client-side)
```
</details>

---

### 2.4 [Dev-3] Network Pages + Users Admin Page
- [ ] Build Network CRUD pages and admin Users page

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/hooks/useNetworks.ts and src/api/types.ts (Network).

Create src/lib/schemas/network.schema.ts with Zod:
  networkCreateSchema: { name: z.string().min(3).max(100), cidr: z.string().regex(/^\d{1,3}(\.\d{1,3}){3}\/\d{1,2}$/, "Invalid CIDR"), is_public: z.boolean().default(false) }

Create src/components/features/networks/NetworkTable.tsx and NetworkForm.tsx
mirroring the VM components above. NetworkForm fields: Name, CIDR (with format hint), Is Public (toggle/checkbox).

Create src/pages/NetworkListPage.tsx and NetworkDetailPage.tsx equivalent to VM pages.
NetworkDetailPage also shows an "Attached VMs" section with a small table of VMs and
Attach/Detach VM buttons (using a Select dropdown listing current user's VMs).

Create src/pages/UserListPage.tsx (admin only):
  - PageLayout title="User Management"
  - DataTable<User> columns: Avatar, Email, Username, Role (badge), Active (checkmark), Created At, Actions
  - Actions: Activate button (for inactive users), Change Role dropdown (user/admin), Delete button
  - All actions use useUsers hooks
  - Shows only to admins (already protected at router level)
```
</details>

---

### 2.5 [Dev-1] Profile Page + Change Password
- [ ] Build user profile and password change

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/hooks/useAuth.ts and src/api/types.ts (UserUpdate, ChangePassword).

Create src/lib/schemas/profile.schema.ts:
  profileUpdateSchema: { first_name: z.string().max(25).optional(), last_name: z.string().max(25).optional(), avatar_url: z.string().url().optional() }
  changePasswordSchema: { old_password: z.string().min(1), new_password: z.string().min(8), confirm_new_password: z.string() }.refine(passwords match)

Create src/pages/ProfilePage.tsx with two tabs (shadcn Tabs):
  Tab 1 "Profile":
    - Shows user avatar (initials fallback), email, username, role badge, member since date
    - Edit form using profileUpdateSchema, calls PATCH /users/{me.id}
    - On success: updates authStore user + shows toast

  Tab 2 "Security":
    - Change password form using changePasswordSchema
    - Calls PATCH /auth/change_password
    - Clears form on success

Create src/components/features/users/UserAvatar.tsx:
  - Props: user: User, size?: 'sm'|'md'|'lg'
  - Shows avatar_url if present, else colored circle with initials (first_name[0] + last_name[0] or username[0])
```
</details>

---

## DAY 3 — Polish, Tests & Deployment

### 3.1 [Dev-2] Responsive Design & Dark Mode
- [ ] Make all pages responsive and add dark mode

<details>
<summary>📎 Copilot Prompt</summary>

```
Read all page components in src/pages/ and src/components/layout/.

1. Responsive audit: ensure all pages work at 375px (mobile), 768px (tablet), 1280px (desktop).
   - Sidebar: hidden on mobile, slide-in drawer triggered by hamburger button
   - DataTable: horizontal scroll wrapper on mobile (<div className="overflow-x-auto">)
   - Forms: full-width on mobile, max-w-lg centered on desktop
   - DashboardPage stats cards: 1 col on mobile, 2 on tablet, 4 on desktop (grid-cols-1 sm:grid-cols-2 lg:grid-cols-4)

2. Dark mode: shadcn/ui supports dark mode via class strategy.
   Create src/store/themeStore.ts (Zustand): { theme: 'light'|'dark', toggle() }
   Persist to localStorage. Apply class="dark" to <html> element.
   Add theme toggle button (sun/moon icon) in Topbar.

3. Page transitions: wrap <Outlet /> in AnimatePresence + motion.div from framer-motion
   with fade + slide-up animation (opacity 0→1, y 10→0, duration 0.2s).
```
</details>

---

### 3.2 [Dev-5] Vitest + RTL Tests
- [ ] Write unit and component tests

<details>
<summary>📎 Copilot Prompt</summary>

```
Read src/components/ui/, src/components/features/, src/hooks/, src/lib/schemas/.

Set up test infrastructure:
  - Install: vitest, @testing-library/react, @testing-library/user-event, msw, @testing-library/jest-dom
  - Create src/tests/setup.ts: import @testing-library/jest-dom, setup MSW server
  - Configure vite.config.ts test section: environment jsdom, setupFiles src/tests/setup.ts

Create src/tests/msw/handlers.ts with MSW v2 handlers for all API endpoints
returning realistic mock data matching the TypeScript types.

Create tests:
  src/tests/unit/schemas.test.ts:
    - vmCreateSchema rejects invalid cpu_cores (0, 65, -1) and accepts valid (1, 32, 64)
    - networkCreateSchema rejects invalid CIDR and accepts valid ones
    - changePasswordSchema rejects when passwords don't match

  src/tests/components/VMStatusBadge.test.tsx:
    - renders correct color class for each status
    - renders correct text label

  src/tests/components/ConfirmDialog.test.tsx:
    - calls onConfirm when confirm button clicked
    - calls onCancel when cancel button clicked
    - shows spinner when isLoading=true

  src/tests/components/LoginPage.test.tsx (with MSW):
    - shows validation errors when submitted empty
    - calls POST /auth/token with correct credentials
    - redirects to /dashboard on success
    - shows error toast on 401 response
```
</details>

---

### 3.3 [Dev-3] Performance Optimization
- [ ] Optimize bundle size and runtime performance

<details>
<summary>📎 Copilot Prompt</summary>

```
Read vite.config.ts and all src/pages/ imports.

1. Vite bundle splitting in vite.config.ts:
   build.rollupOptions.output.manualChunks:
     'vendor-react': ['react', 'react-dom', 'react-router-dom']
     'vendor-query': ['@tanstack/react-query']
     'vendor-ui': ['@radix-ui/...all radix packages...']
     'vendor-form': ['react-hook-form', 'zod', '@hookform/resolvers']

2. All pages already lazy loaded via React.lazy(). Ensure Suspense fallback
   in router uses a full-page Skeleton (src/components/ui/PageSkeleton.tsx).

3. In VMListPage and NetworkListPage wrap sorted/filtered array derivation in useMemo.
   Wrap event handlers (onPageChange, onSearch, onDelete) in useCallback.

4. Debounce search input: create src/hooks/useDebounce.ts:
   function useDebounce<T>(value: T, delay: number): T
   Use in list pages: const debouncedSearch = useDebounce(searchInput, 300)

5. Add React Query global config in main.tsx:
   staleTime: 60_000, gcTime: 5 * 60_000, retry: 1
```
</details>

---

### 3.4 [Dev-4] UX Polish & Error States
- [ ] Add notifications, error pages, and UX improvements

<details>
<summary>📎 Copilot Prompt</summary>

```
Read all pages in src/pages/ and src/components/.

1. Toast notifications: Integrate shadcn Toaster in src/main.tsx.
   Create src/lib/toast.ts with helper functions:
     toast.success(message), toast.error(message), toast.info(message)
   Use in all mutation hooks (already planned in useVMs/useNetworks hooks).

2. Create src/pages/NotFoundPage.tsx:
   - "404 — Page Not Found" with a fun illustration (SVG inline)
   - "Go to Dashboard" button

3. Create src/components/ui/PageError.tsx:
   - Props: error: Error, retry?: () => void
   - Shows error message + Retry button
   Use as errorElement in router for each route.

4. Global error boundary: update src/main.tsx ErrorBoundary to show PageError
   with a "Reload" button that calls window.location.reload().

5. Add keyboard shortcuts:
   - Escape: close any open dialog (already handled by shadcn Dialog)
   - Ctrl+K (or Cmd+K): focus search input on list pages
   Implement via useEffect + keydown listener in a src/hooks/useKeyboardShortcut.ts hook.

6. Breadcrumb component: src/components/ui/Breadcrumbs.tsx
   - Uses useMatches() from react-router-dom
   - Each route has a handle: { breadcrumb: string } in the router config
   - Renders shadcn Breadcrumb at top of AppLayout
```
</details>

---

### 3.5 [Dev-1] Frontend README + CI/CD
- [ ] Generate README_FRONTEND.md and GitHub Actions

<details>
<summary>📎 Copilot Prompt</summary>

```
Read the entire frontend project structure, all pages, components, vite.config.ts, package.json.

Generate README_FRONTEND.md with:
1. Project title + tech stack badges
2. Architecture overview: layers diagram (Pages → Hooks → API Client → Backend)
3. Quick Start:
   cd frontend / cp .env.example .env / npm install / npm run dev
4. Environment variables table: VITE_API_URL (required), VITE_APP_NAME
5. Project structure tree explanation
6. Available scripts: dev, build, preview, test, test:coverage, lint
7. Pages & Routes table: Path | Page | Auth Required | Description
8. Component library notes (shadcn/ui components used)
9. State management: Zustand stores explained
10. Deployment to Vercel: config + env variables

Generate frontend/.env.example:
  VITE_API_URL=http://localhost:8000
  VITE_APP_NAME=CloudIaaS

Generate .github/workflows/frontend-ci.yml:
  trigger: push/PR to main and dev
  jobs:
    build-and-test:
      runs-on: ubuntu-latest
      steps:
        - checkout
        - setup node 20
        - npm ci
        - npm run lint (eslint)
        - npx tsc --noEmit (type check)
        - npm run test (vitest --run)
        - npm run build (vite build)
```
</details>

---

## Pages & Routes Summary

| Path | Page | Auth | Role |
|------|------|------|------|
| `/login` | LoginPage | ❌ | — |
| `/register` | RegisterPage | ❌ | — |
| `/register/confirm` | ConfirmEmailPage | ❌ | — |
| `/dashboard` | DashboardPage | ✅ | Any |
| `/vms` | VMListPage | ✅ | Any |
| `/vms/:id` | VMDetailPage | ✅ | Any |
| `/vms/:id/edit` | VMEditPage | ✅ | Owner/Admin |
| `/networks` | NetworkListPage | ✅ | Any |
| `/networks/:id` | NetworkDetailPage | ✅ | Any |
| `/profile` | ProfilePage | ✅ | Any |
| `/users` | UserListPage | ✅ | Admin |
| `*` | NotFoundPage | ❌ | — |

## Component Architecture

```
src/
├── pages/              ← Route-level components (lazy loaded)
├── components/
│   ├── ui/             ← Generic: Button, Input, DataTable, Modal…
│   ├── features/
│   │   ├── vms/        ← VMTable, VMForm, VMStatusBadge
│   │   ├── networks/   ← NetworkTable, NetworkForm
│   │   └── users/      ← UserAvatar, UserTable
│   └── layout/         ← AppLayout, Sidebar, Topbar, Breadcrumbs
├── hooks/              ← useVMs, useNetworks, useUsers, useAuth
├── store/              ← authStore (Zustand), themeStore
├── api/                ← client.ts, types.ts, vms.ts, networks.ts…
└── lib/schemas/        ← Zod schemas per entity
```
