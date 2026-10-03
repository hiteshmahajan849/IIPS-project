// Renders the HOD dashboard's course-comparison bar chart and sentiment
// trend-over-semesters line chart. `courses` and `trend` are injected
// inline by hod/dashboard.html.
document.addEventListener("DOMContentLoaded", () => {
  if (typeof courses === "undefined") return;

  const courseCanvas = document.getElementById("courseChart");
  if (courseCanvas) {
    new Chart(courseCanvas, {
      type: "bar",
      data: {
        labels: courses.map((c) => c.code),
        datasets: [{
          label: "Avg rating",
          data: courses.map((c) => c.avg_rating || 0),
          backgroundColor: "#2d5579",
        }],
      },
      options: { scales: { y: { beginAtZero: true, max: 5 } }, plugins: { legend: { display: false } } },
    });
  }

  const trendCanvas = document.getElementById("trendChart");
  if (trendCanvas) {
    new Chart(trendCanvas, {
      type: "line",
      data: {
        labels: trend.map((t) => "Sem " + t.semester),
        datasets: [
          { label: "Positive", data: trend.map((t) => t.positive), borderColor: "#0d9488", tension: 0.3 },
          { label: "Neutral", data: trend.map((t) => t.neutral), borderColor: "#a16207", tension: 0.3 },
          { label: "Negative", data: trend.map((t) => t.negative), borderColor: "#b91c1c", tension: 0.3 },
        ],
      },
      options: { plugins: { legend: { position: "bottom" } } },
    });
  }
});
