# Product Requirements Document (PRD) - Audit & Refactoring

## 1. Audit Overview & Gap Analysis

Based on the code audit and user requirements, the following gaps have been identified:

### 1.1. Credit System & Pricing
*   **Current State**: 
    *   `Subscription` has `credits_total` (based on package).
    *   1 Booking = 1 Credit (hardcoded).
    *   `Modality` has no definition of cost.
*   **Requirement**: 
    *   Different modalities must cost different amounts (e.g., Weights = 10, Electro = 30).
    *   Admins must configure this.
    *   Store simulation for weekly class estimates.
*   **Gap**: Missing `credits_cost` in `Modality`. Missing logic to deduct variable credits.

### 1.2. Recurring Booking
*   **Current State**: 
    *   `RecurringBooking` model exists.
    *   Logic limits creating bookings beyond `subscription.end_date`.
*   **Requirement**: 
    *   "Option to schedule recurrently (Every Monday)".
    *   "Limited to days until package expiration".
*   **Status**: Mostly implemented. UI may need verification to ensure it's accessible and clear.

### 1.3. Instructor Features
*   **Current State**: 
    *   `User` model has 'instructor' role.
    *   No dedicated UI to register instructors found in Admin.
    *   No specific Instructor Dashboard for check-ins.
*   **Requirement**: 
    *   Admin must be able to register instructors.
    *   Instructor needs a simple "Check-in" screen for students.
*   **Gap**: Missing Admin Route/Template for Instructor creation. Missing Instructor Dashboard.

### 1.4. UI/UX & Navigation
*   **Current State**: 
    *   `base.html` has no built-in navigation bar.
    *   User reports missing "Back" buttons and top menu.
*   **Requirement**: 
    *   All screens must have navigation/menu.
    *   "Back" options on deep pages.
*   **Gap**: Navigation component needs to be added globally or per layout.

---

## 2. Implementation Plan

The implementation will be divided into 3 stages. Each stage includes the prompt to be executed.

### Stage 1: Core Credit System Refactoring
**Goal**: Implement variable credit costs for modalities and update booking logic.

**Tasks**:
1.  **Database Migration**: Add `credits_cost` to `Modality`. Add `credits_cost` to `Booking` (for history).
2.  **Admin UI**: Allow editing `credits_cost` in Modality form.
3.  **Booking Logic**: 
    *   Update `Booking.validate_booking` to check `subscription.credits_remaining >= schedule.modality.credits_cost`.
    *   Update creation logic to deduct `schedule.modality.credits_cost`.
    *   Update refund logic to refund `booking.cost_at_booking`.
4.  **Recurring Logic**: Update `RecurringBooking` to respect variable costs.

**Prompt for Stage 1**:
```markdown
You are tasked with refactoring the Credit System of the Academy Management Application.
Follow these steps:

1.  **Modify Models**:
    *   Update `app/models/modality.py`: Add `credits_cost = db.Column(db.Integer, default=1, nullable=False)`.
    *   Update `app/models/booking.py`: Add `cost_at_booking = db.Column(db.Integer, nullable=False, default=1)`.
    *   *Note*: Ensure to create a migration or update the DB schema accordingly (use direct SQL or `db.create_all()` logic if applicable).

2.  **Update Booking Logic (`app/routes/student.py` & `app/models/booking.py`)**:
    *   In `Booking.validate_booking`: Check if `subscription.credits_remaining >= schedule.modality.credits_cost`.
    *   In `book_class` route:
        *   When creating `Booking`, set `cost_at_booking = schedule.modality.credits_cost`.
        *   Deduct `schedule.modality.credits_cost` from `subscription.credits_used`.
        *   **Crucial**: Do NOT change `credits_used` by 1. Use the modality cost.
    *   In `cancel_booking` route:
        *   Refund `booking.cost_at_booking` (or `booking.schedule.modality.credits_cost` if cost_at_booking is null).

3.  **Update Recurring Booking (`app/models/recurring_booking.py`)**:
    *   In `can_create_next`: Check if `subscription.credits_remaining >= self.schedule.modality.credits_cost`.
    *   In `create_next_booking`: Deduct `self.schedule.modality.credits_cost` and set `cost_at_booking`.

4.  **Admin Modality Management**:
    *   Update `app/routes/admin/modalities.py` (or equivalent) to allow editing `credits_cost`.
    *   Update the template for creating/editing modalities to include this field.

5.  **Store Simulation**:
    *   In `app/models/package.py`, update `price_per_credit` logic to be meaningful or remove if unused.

Perform these changes carefully to ensure the integrity of the credit system.
```

---

### Stage 2: Instructor Module (Registration & Dashboard)
**Goal**: Enable Instructor registration and a simple Check-in flow.

**Tasks**:
1.  **Admin - create Instructor**:
    *   Add route/form in Admin to create a user with `role='instructor'`.
2.  **Instructor Dashboard**:
    *   Create `app/routes/instructor.py`.
    *   Route `/instructor` (Home): Show today's classes for the logged-in instructor.
    *   Show list of students in each class with a "Check-in" button.
    *   Action: Check-in button calls API to mark `Booking` as `COMPLETED` (Attendance).

**Prompt for Stage 2**:
```markdown
Implement the Instructor Module.

1.  **Instructor Registration (Admin)**:
    *   Check `app/routes/admin/` for user management. If not present, create a simple route `/admin/instructors/new` to create a User with `role='instructor'`.
    *   Inputs: Name, Email, Password, Phone.

2.  **Instructor Dashboard**:
    *   Create a new Blueprint `instructor_bp` in `app/routes/instructor.py`.
    *   Register it in `app/__init__.py`.
    *   **Route `/instructor/dashboard`**:
        *   Fetch `ClassSchedule`s for `current_user` (Instructor) that match `weekday` of today.
        *   For each schedule, fetch `Booking`s with `date == today` and `status == CONFIRMED`.
    *   **Template `templates/instructor/dashboard.html`**:
        *   Simple, mobile-friendly card layout.
        *   List classes: "08:00 - Musculação".
        *   Inside class: List Students.
        *   Button "Check-in" next to student name.
    *   **Check-in Action**:
        *   Route `/instructor/checkin/<booking_id>`.
        *   Updates booking status to `COMPLETED`.
        *   Adds XP to student (already in `checkin()` method of Booking).
        *   Flash success message and return to dashboard.

3.  **Navigation**:
    *   Ensure the Instructor Dashboard is the default home for `instructor` role login.
```

---

### Stage 3: Shop Simulation & UI Polish
**Goal**: Address Store simulation and Navigation issues.

**Tasks**:
1.  **Store Simulation**:
    *   In `shop` templates, add a Calculator.
    *   Inputs: "How many times/week?" for each Modality.
    *   Calculation: `(Weekly_Frequency * Modality_Cost * 4)`. Compare with Package Credits.
    *   Display: "With Package X (400 Credits), you can train: A + B...".
2.  **Navigation**:
    *   Create `navbar.html` include.
    *   Add "Back" buttons to all Detail pages (`subscription_detail`, `booking_detail`, etc.).

**Prompt for Stage 3**:
```markdown
Refine the Shop and Navigation.

1.  **Shop Simulation**:
    *   In `app/templates/shop/index.html` (or wherever packages are listed):
    *   Add a "Simulator" section.
    *   Fetch all `Modalities` and their `credits_cost` (pass to template).
    *   JS Logic: Allow user to input "Classes per week" for each modality.
    *   Calculate `Total Monthly Credits Needed = Sum(Freq * Cost * 4)`.
    *   Highlight which Packages cover this need.
    *   *Specifically*: Show feedback "Buying Package R$400 allows: 2x Electro + 2x Weighs" (based on the math).

2.  **Navigation Audit**:
    *   Create `app/templates/includes/navbar.html` with links: Dashboard, Schedule, Shop, Profile, Logout.
    *   Include this in `base.html` (or ensure it's in layout).
    *   Add specific "Back" buttons (history.back() or link to parent) in:
        *   `subscription_detail.html`
        *   `schedule.html`
        *   `recurring_form.html`

3.  **Best Practices**:
    *   Ensure all forms have CSRF protection.
    *   Ensure mobile responsiveness (Bootstrap classes).
```
