const themeToggle = document.querySelector("#theme-toggle");

function applyTheme(theme) {
  if (theme === "dark") {
    document.documentElement.dataset.theme = "dark";
  } else {
    document.documentElement.dataset.theme = "light";
  }
}

if (themeToggle) {
  const savedTheme = localStorage.getItem("theme") || "light";

  applyTheme(savedTheme);
  themeToggle.checked = savedTheme === "dark";

  themeToggle.addEventListener("change", () => {
    const nextTheme = themeToggle.checked ? "dark" : "light";
    localStorage.setItem("theme", nextTheme);
    applyTheme(nextTheme);
  });
}
