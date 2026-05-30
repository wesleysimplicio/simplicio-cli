# Scratch Recipe Benchmark

synthetic declarative recipe benchmark; validates match-before-planner coverage and plan schema integrity but does not replace the real 50-scratch release gate

## Summary

- cases: 50
- matched: 30
- match rate: 60.00%
- valid recipe plans: 30
- planner calls saved: 30

## Release Gate Status

- fifty_goal_corpus: True
- recipe_match_ge_40: True
- matched_plans_valid: True
- expected_match_accuracy_100: True
- real_scratch_corpus: False
- llm_pass_rate_baseline_present: False

## Cases

| stack | goal | recipe | matched | plan_valid |
| --- | --- | --- | --- | --- |
| py-fastapi | CRUD API for Unit | crud-resource | True | True |
| py-fastapi | REST API for Invoice | crud-resource | True | True |
| py-fastapi | CRUD API for Visitor | crud-resource | True | True |
| py-fastapi | REST API for AmenityBooking | crud-resource | True | True |
| py-fastapi | CRUD API for Vendor | crud-resource | True | True |
| py-fastapi | admin panel for Booking | admin-crud | True | True |
| py-fastapi | admin panel for Document | admin-crud | True | True |
| py-fastapi | admin panel for Resident | admin-crud | True | True |
| py-fastapi | add JWT auth | auth-jwt | True | True |
| py-fastapi | login with JWT | auth-jwt | True | True |
| py-fastapi | authentication with JWT | auth-jwt | True | True |
| py-fastapi | REST API for ParkingSpace | crud-resource | True | True |
| py-fastapi | CRUD API for PackageDelivery | crud-resource | True | True |
| py-fastapi | admin panel for Announcement | admin-crud | True | True |
| py-fastapi | CRUD API for Payment | crud-resource | True | True |
| ts-nextjs | Manage Product with CRUD | crud-resource | True | True |
| ts-nextjs | CRUD page for Unit | crud-resource | True | True |
| ts-nextjs | Manage Invoice with CRUD | crud-resource | True | True |
| ts-nextjs | CRUD page for Visitor | crud-resource | True | True |
| ts-nextjs | Manage Vendor with CRUD | crud-resource | True | True |
| ts-nextjs | admin CRUD for Tenant | admin-crud | True | True |
| ts-nextjs | backoffice to manage Subscription | admin-crud | True | True |
| ts-nextjs | admin CRUD for Booking | admin-crud | True | True |
| ts-nextjs | authentication with JWT | auth-jwt | True | True |
| ts-nextjs | login with JWT | auth-jwt | True | True |
| ts-nextjs | add JWT auth | auth-jwt | True | True |
| ts-nextjs | Manage Document with CRUD | crud-resource | True | True |
| ts-nextjs | CRUD page for ParkingSpace | crud-resource | True | True |
| ts-nextjs | backoffice to manage Payment | admin-crud | True | True |
| ts-nextjs | Manage AccessDevice with CRUD | crud-resource | True | True |
| py-fastapi | Build a recommendation engine for movies | - | False | False |
| py-fastapi | Analyze CSV exports overnight | - | False | False |
| py-fastapi | Create websocket chat rooms | - | False | False |
| py-fastapi | Generate a billing report | - | False | False |
| py-fastapi | Import legacy XML data | - | False | False |
| py-fastapi | Build a workflow scheduler | - | False | False |
| py-fastapi | Create an ML inference gateway | - | False | False |
| py-fastapi | Synchronize LDAP groups | - | False | False |
| py-fastapi | Build a search ranking service | - | False | False |
| py-fastapi | Create a geocoding proxy | - | False | False |
| ts-nextjs | Create a marketing landing page | - | False | False |
| ts-nextjs | Render a public docs site | - | False | False |
| ts-nextjs | Add image optimization pipeline | - | False | False |
| ts-nextjs | Design a pricing comparison table | - | False | False |
| ts-nextjs | Build a chart dashboard | - | False | False |
| ts-nextjs | Create a theme editor | - | False | False |
| ts-nextjs | Build a map explorer | - | False | False |
| ts-nextjs | Add offline-first sync | - | False | False |
| ts-nextjs | Create a video playlist page | - | False | False |
| ts-nextjs | Build an onboarding wizard | - | False | False |
