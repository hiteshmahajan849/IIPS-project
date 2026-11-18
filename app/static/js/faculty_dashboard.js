// Faculty dashboard charts. Colours come from the shared CSS design tokens.
document.addEventListener("DOMContentLoaded", () => {
  if (typeof sentimentData === "undefined" || typeof Chart === "undefined") return;

  const styles = getComputedStyle(document.documentElement);
  const token = (name) => styles.getPropertyValue(name).trim();
  const colours = {
    primary: token("--color-primary-800"),
    primarySoft: token("--color-primary-700"),
    positive: token("--color-positive"),
    neutral: token("--color-neutral"),
    negative: token("--color-negative"),
    grid: token("--color-border"),
    text: token("--color-text-muted"),
  };
  Chart.defaults.font.family = 'Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif';
  Chart.defaults.color = colours.text;

  const showEmpty = (canvas, message = "No data yet") => {
    if (!canvas) return;
    canvas.style.display = "none";
    const empty = document.createElement("div");
    empty.className = "chart-empty";
    empty.textContent = message;
    canvas.parentElement.appendChild(empty);
  };

  const sentimentCanvas = document.getElementById("sentimentChart");
  const sentimentValues = ["positive", "neutral", "negative"].map((label) => sentimentData[label] || 0);
  if (sentimentCanvas && sentimentValues.some(Boolean)) {
    new Chart(sentimentCanvas, {
      type: "doughnut",
      data: {
        labels: ["Positive", "Neutral", "Negative"],
        datasets: [{ data: sentimentValues, backgroundColor: [colours.positive, colours.neutral, colours.negative], borderWidth: 0 }],
      },
      options: {
        cutout: "68%",
        plugins: {
          legend: { position: "bottom", labels: { usePointStyle: true, padding: 18 } },
          tooltip: { callbacks: { label: (context) => ` ${context.label}: ${context.raw} responses` } },
        },
      },
    });
  } else {
    showEmpty(sentimentCanvas);
  }

  const aspectCanvas = document.getElementById("aspectChart");
  const labels = Object.keys(aspectData || {});
  if (aspectCanvas && labels.length) {
    new Chart(aspectCanvas, {
      type: "bar",
      data: {
        labels: labels.map((label) => label.charAt(0).toUpperCase() + label.slice(1)),
        datasets: [{ label: "Average score", data: labels.map((label) => aspectData[label]), backgroundColor: colours.primary, borderRadius: 7, borderSkipped: false }],
      },
      options: {
        scales: { y: { beginAtZero: true, max: 5, grid: { color: colours.grid }, ticks: { stepSize: 1 } }, x: { grid: { display: false } } },
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context) => ` ${context.raw} / 5` } } },
      },
    });
  } else {
    showEmpty(aspectCanvas);
  }
});
