// Invalid — 8 background colors in a single chart (exceeds 7-color limit)
import Chart from "chart.js/auto";

const ctx = document.getElementById("chart").getContext("2d");

new Chart(ctx, {
  type: "bar",
  data: {
    labels: ["A", "B", "C", "D", "E", "F", "G", "H"],
    datasets: [
      {
        label: "Categories",
        data: [10, 20, 30, 40, 50, 60, 70, 80],
        backgroundColor: [
          "#4e79a7",
          "#f28e2b",
          "#e15759",
          "#76b7b2",
          "#59a14f",
          "#edc948",
          "#b07aa1",
          "#ff9da7",
        ],
      },
    ],
  },
  options: {
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  },
});
