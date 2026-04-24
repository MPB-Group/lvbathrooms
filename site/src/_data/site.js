module.exports = {
  title: "Bathrooms by LV",
  tagline: "Luxury bathrooms at affordable prices",
  year: new Date().getFullYear(),
  url: "https://lvbathrooms.co.uk",
  description:
    "A local Warrington bathroom contractor with extensive experience in all bathroom renovations and a reputation for delivering quality and value.",
  email: "WeCare@LVBathrooms.co.uk",
  phone: "07725 746 529",
  landline: "01925 457024",
  location: "Warrington, Cheshire",
  social: {
    // Add real handles when known; these are placeholders.
    facebook: "",
    instagram: "",
  },
  nav: [
    { label: "Home", url: "/" },
    { label: "Projects", url: "/projects/" },
    { label: "Services", url: "/#services" },
    { label: "Contact", url: "/contact/" },
  ],
  // The three service cards shown on the homepage
  services: [
    {
      title: "Emergency Repairs",
      slug: "emergency-repairs",
      tagline: "Fast, honest help when something gives way",
      href: "/emergency-repairs/",
    },
    {
      title: "Refurbishment",
      slug: "refurbishment",
      tagline: "Full makeover to your exact specification",
      href: "/refurbishment/",
    },
    {
      title: "Creation",
      slug: "bathroom-creation",
      tagline: "New bathrooms from unused spaces",
      href: "/bathroom-creation/",
    },
  ],
  // Counter stats under the service cards
  counters: [
    { value: 500, label: "Bathrooms" },
    { value: 250, label: "Cloakrooms" },
    { value: 750, label: "En Suites" },
  ],
  // The two homepage testimonials — TO REPLACE once real customer photos
  // are provided (current WP site uses Futurio demo stock faces)
  testimonials: [
    {
      body:
        "Liam and his team previously designed and installed bathrooms at our current and previous homes and have always done a fantastic job, so when we needed a complete bathroom we went straight to LV.",
      name: "Vicky & Michael Watson",
      location: "",
    },
    {
      body:
        "We had a complete bathroom refit carried out by Liam. I really couldn’t recommend him more highly, from start to finish his work is second to none. He really loves what he does.",
      name: "Mariah and Dickie",
      location: "Latchford",
    },
  ],
};
