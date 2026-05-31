// Invalid — bar chart used for ISO date time-series data (should be line chart)
import Chart from "chart.js/auto";

const ctx = document.getElementById("chart").getContext("2d");

new Chart(ctx, {
  type: "bar",
  data: {
    labels: ["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01"],
    datasets: [
      {
        label: "Revenue",
        data: [12000, 15000, 9000, 18000],
        backgroundColor: "#4e79a7",
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
