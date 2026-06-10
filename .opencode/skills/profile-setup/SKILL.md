---
name: profile-setup
description: Guides the candidate through populating and maintaining their career profile. Triggers on: setup, set up profile, configure profile, update profile, edit profile, change profile, profile setup, fill in profile, reset profile, my profile
---

# Profile Setup & Management

Your purpose is to help the candidate populate, validate, and maintain their career profile across all profile files in the repo.

## Profile File Map

| File | Contents |
|------|----------|
| `OPENDOC.md` | Identity, education, experience, skills, certifications, publications, awards, behavioral profile (summary), passions, target sectors, deal-breakers |
| `.opencode/skills/job-application-assistant/01-candidate-profile.md` | Extended identity (phone, email, LinkedIn, GitHub), detailed education, detailed experience, independent projects, detailed skills, publications, awards, references |
| `.opencode/skills/job-application-assistant/02-behavioral-profile.md` | Behavioral assessment results, strengths, growth areas, ideal environments |
| `.opencode/skills/job-application-assistant/03-writing-style.md` | Writing style rules (static; rarely modified) |
| `.opencode/skills/job-application-assistant/04-job-evaluation.md` | Skill match areas (strong/moderate/weak), experience match domains, career goals, motivation filter, life situation alignment |
| `.opencode/skills/job-application-assistant/05-cv-templates.md` | CV template rules (static; not modified during setup) |
| `.opencode/skills/job-application-assistant/06-cover-letter-templates.md` | Cover letter template rules (static; not modified during setup) |
| `.opencode/skills/job-application-assistant/07-interview-prep.md` | STAR examples, tough questions (populated during setup, updated with experience) |

## Scenarios

### Initial Population
Guide the user through filling in every section, starting with identity and contact details, then education and experience, then skills, then career goals and preferences. Replace every `[PLACEHOLDER_TOKEN]` across all files with the user's actual information. Ask one section at a time, conversationally. After populating a section, show the user what was written before moving on.

### Validation
After any change, check completeness: flag any remaining `[PLACEHOLDER]` tokens. Check that `OPENDOC.md` and `01-candidate-profile.md` are consistent — no contradictory job titles, dates, or contact details. Check that `04-job-evaluation.md` scoring dimensions reference real profile data, not placeholders. Print a profile completeness summary. Validation is read-only inspection unless the user explicitly asks you to make changes.

### Update Existing Profile
When the user wants to modify a section, identify which file(s) contain it from the file map above, then update both files if the section spans multiple:

- **Add experience**: Update Professional Experience in `OPENDOC.md` and `01-candidate-profile.md`. Add experience domains to `04-job-evaluation.md` if the role expands capability.
- **Update skills**: Update Technical Skills in `OPENDOC.md` and `01-candidate-profile.md`. Update skill match areas in `04-job-evaluation.md`.
- **Change career goals**: Update career goals in `04-job-evaluation.md` and passions/target sectors in `OPENDOC.md`.
- **Update deal-breakers**: Update `OPENDOC.md`. Ensure they are specific and actionable.
- **Update behavioral traits**: Update `OPENDOC.md` and `02-behavioral-profile.md`.
- **Add publication/award**: Update both `OPENDOC.md` and `01-candidate-profile.md`.

## Rules
- Never overwrite user-filled data without confirmation.
- Deal-breakers must be specific and actionable, not generic.
- After any update, offer to run validation.
