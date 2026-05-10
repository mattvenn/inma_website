# inspirational websites

https://www.moving-pathways.com/
https://www.terapiacreativa.es/
https://estiolabarri.com/

# requirements

* dual languages - english and spanish. 
* use photos/inma_portrait.jpg as the therapist portrait photo
* use photos from the photos directory to illustrate the sections
* use testimonials from the testimonial documents in ./testimonials

# website description

* simple static website, mostly one page
* it's for a movement therapist. 
* mostly woment clients. 
* should be calm, accents of colour. 

# tech stuff

* hosted at https://www.inmapiquerasramos.com/
* put a bunch of config in an easy to change file, fonts, colours, themes
* anticipated that there will be an 'upcoming events' directory that will need to be easy to update
* should work well on phone and computer. 50% will use the phone.

# website content

for each section, use information in text/english.odt and text/spanish.odt

* one sentence idea: move into being - a place from which to find, heal and transform yourself.
* 'services offered' - one on ones, group sessions, supervision. these could be cards where more context is available if selected or hovered over.
* 'testimonials' a set of photos, quotes, video cards. 'contact / booking' all the usual stuff.
* contact form, newsletter signup link, linkedin, instagram connectors

# therapist information

- therapist name: Inma Piqueras Ramos, located in Valencia, Spain
- registered Dance Movement Psychotherapist (DMP), Private Practitioner, Clinical Supervisor and Trainer.
- https://www.linkedin.com/in/inma-piqueras-ramos-81144217/?originalSubdomain=es
- https://www.instagram.com/inma.piqueras.ramos/

# theme

- palette: Soft sage & clay (calming greens, dusty pink)
- type_feel: Editorial serif + clean sans (warm, considered)

---

# what has been built (context for future sessions)

## files
- `index.html` — single-page site, all sections in one file
- `style.css` — all styles
- `config.css` — design tokens only: colours, fonts, layout, animation timings. Edit this to change look and feel.
- `script.js` — vanilla JS: language toggle, active nav, services expand, photo cycling, parallax, events loader
- `events/events.json` — empty array; add event objects here to show upcoming events section

## images
Images are organised into subfolders inside `images/`:
- `images/abstract/` — abstract textures used as section dividers and testimonials background
- `images/body_mapping/` — used for body mapping service and supervision
- `images/dmp/` — used for dance movement psychotherapy service
- `images/training_and_workshops/` — used for training service and about portrait
- `images/inma_portrait.png` — not currently used on the site
- `images/training_and_workshops/inma_teaching.JPG` — current about section portrait
- `images/body_mapping/green_foot.jpg` — current hero background image

## design decisions made
- Fonts: Cormorant Garamond (serif headings/quotes) + DM Sans (body/UI), loaded from Google Fonts
- Hero: full-bleed background image, dark gradient overlay, three-line staggered title (Move / INTO / Being) with parallax scroll effect
- Services: four full-width horizontal strips, photo alternates left/right. Click opens a full-width text drawer below. Photos cross-fade through folder images (5s transition, 5s hold) while expanded.
- Testimonials: auto-scrolling carousel (65s loop), 7 testimonials per language. Background is `abstract_cloth.JPG` at 55% opacity overlay.
- Section dividers: two thin parallax image slices between sections (abstract hand between services→about; removed others)
- Language toggle: EN/ES pill in nav. Saves to localStorage. Detects browser language on first visit. Text uses `data-en`/`data-es` attributes (JS-swapped) for inline strings; `.lang-en`/`.lang-es` CSS classes for block elements.
- Active nav: IntersectionObserver highlights current section link with sage underline
- Location shown: Valencia, Spain (also available online). No phone, no public email.
- Contact form: Formspree — action URL in index.html still contains `YOUR_FORM_ID` placeholder, needs replacing.

## still to do / placeholders
- **Formspree ID**: replace `YOUR_FORM_ID` in the contact form action attribute
- **Newsletter link**: search for `YOUR_NEWSLETTER_LINK` in index.html and replace with Mailchimp/ConvertKit URL
- **Testimonial videos**: inspiration.md mentioned video cards but these were not built
- **Favicon**: currently an emoji leaf SVG inline — replace with a proper favicon file
- **SEO**: meta description is generic; og:image, og:title etc not set
- **Events**: when Inma has events, add objects to `events/events.json` — the section auto-shows when the array is non-empty. Format: `{ "date": "2026-06-15", "title": "...", "description": "...", "location": "...", "link": "...", "linkText": "..." }`
- **Mobile testing**: site is responsive but has not been tested on real devices; 50% of visitors expected on phone

