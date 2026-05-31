// Invalid pie chart — 6 slices violates the 5-slice maximum rule
import Chart from "chart.js/auto";

const ctx = document.getElementById("chart").getContext("2d");

new Chart(ctx, {
  type: "pie",
  data: {
    labels: ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"],
    datasets: [
      {
        data: [30, 20, 15, 12, 13, 10],
        backgroundColor: [
          "#4e79a7",
          "#f28e2b",
          "#e15759",
          "#76b7b2",
          "#59a14f",
          "#edc948",
        ],
      },
    ],
  },
});
