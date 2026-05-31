// Invalid: uses pure red + pure green to distinguish series — colorblind unsafe (deuteranopia)
import Chart from "chart.js/auto";

const ctx = document.getElementById("chart").getContext("2d");

new Chart(ctx, {
  type: "line",
  data: {
    labels: ["Jan", "Feb", "Mar", "Apr"],
    datasets: [
      {
        label: "Northeast",
        data: [125000, 131000, 128000, 142000],
        borderColor: "#2ca02c",
        backgroundColor: "#2ca02c",
      },
      {
        label: "Southeast",
        data: [98000, 92000, 87000, 89000],
        borderColor: "#d62728",
        backgroundColor: "#d62728",
      },
    ],
  },
  options: {
    scales: { y: { beginAtZero: true } },
    plugins: { legend: { display: true } },
  },
});
