document.addEventListener("DOMContentLoaded", () => {
  // Simple micro-interaction: animate cards on hover via JS class
  document.querySelectorAll(".issue-card").forEach((card) => {
    card.addEventListener("mouseenter", () => card.classList.add("hovered"));
    card.addEventListener("mouseleave", () => card.classList.remove("hovered"));
  });
});




