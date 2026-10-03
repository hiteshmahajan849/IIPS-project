// Renders the faculty dashboard's sentiment donut and aspect bar charts.
// `sentimentData` and `aspectData` are injected inline by faculty/dashboard.html.
document.addEventListener("DOMContentLoaded", () => {
  if (typeof sentimentData === "undefined") return;

  const sentimentCanvas = document.getElementById("sentimentChart");
  if (sentimentCanvas) {
    new Chart(sentimentCanvas, {
      type: "doughnut",
      data: {
        labels: ["Positive", "Neutral", "Negative"],
        datasets: [{
          data: [
            sentimentData.positive || 0,
            sentimentData.neutral || 0,
            sentimentData.negative || 0,
          ],
          backgroundColor: ["#0d9488", "#a16207", "#b91c1c"],
        }],
      },
      options: { plugins: { legend: { position: "bottom" } } },
    });
  }

  const aspectCanvas = document.getElementById("aspectChart");
  if (aspectCanvas) {
    const labels = Object.keys(aspectData);
    new Chart(aspectCanvas, {
      type: "bar",
      data: {
        labels: labels.map((l) => l.charAt(0).toUpperCase() + l.slice(1)),
        datasets: [{
          label: "Average score",
          data: labels.map((l) => aspectData[l]),
          backgroundColor: "#2d5579",
        }],
      },
      options: { scales: { y: { beginAtZero: true, max: 5 } }, plugins: { legend: { display: false } } },
    });
  }
});
