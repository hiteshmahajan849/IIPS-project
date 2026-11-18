// HOD dashboard charts. Colours come from the shared CSS design tokens.
document.addEventListener("DOMContentLoaded", () => {
  if (typeof courses === "undefined" || typeof Chart === "undefined") return;

  const styles = getComputedStyle(document.documentElement);
  const token = (name) => styles.getPropertyValue(name).trim();
  const colours = {
    primary: token("--color-primary-800"),
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

  const courseCanvas = document.getElementById("courseChart");
  if (courseCanvas && courses.length) {
    new Chart(courseCanvas, {
      type: "bar",
      data: {
        labels: courses.map((course) => course.code),
        datasets: [{ label: "Average rating", data: courses.map((course) => course.avg_rating || 0), backgroundColor: colours.primary, borderRadius: 7, borderSkipped: false }],
      },
      options: {
        scales: { y: { beginAtZero: true, max: 5, grid: { color: colours.grid }, ticks: { stepSize: 1 } }, x: { grid: { display: false } } },
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context) => ` ${context.raw} / 5` } } },
      },
    });
  } else {
    showEmpty(courseCanvas);
  }

  const trendCanvas = document.getElementById("trendChart");
  if (trendCanvas && trend.length) {
    new Chart(trendCanvas, {
      type: "line",
      data: {
        labels: trend.map((item) => "Sem " + item.semester),
        datasets: [
          { label: "Positive", data: trend.map((item) => item.positive), borderColor: colours.positive, backgroundColor: colours.positive, tension: 0.3, pointRadius: 4 },
          { label: "Neutral", data: trend.map((item) => item.neutral), borderColor: colours.neutral, backgroundColor: colours.neutral, tension: 0.3, pointRadius: 4 },
          { label: "Negative", data: trend.map((item) => item.negative), borderColor: colours.negative, backgroundColor: colours.negative, tension: 0.3, pointRadius: 4 },
        ],
      },
      options: {
        scales: { y: { beginAtZero: true, grid: { color: colours.grid }, ticks: { precision: 0 } }, x: { grid: { display: false } } },
        plugins: { legend: { position: "bottom", labels: { usePointStyle: true, padding: 18 } }, tooltip: { callbacks: { label: (context) => ` ${context.raw} responses` } } },
      },
    });
  } else {
    showEmpty(trendCanvas);
  }
});
