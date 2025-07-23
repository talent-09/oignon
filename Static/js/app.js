let tempChart, humChart, gazChart;

function createCharts(labels, tempData, humData, gazData) {
  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: '#444' }
      }
    },
    plugins: {
      legend: {
        labels: {
          color: '#1c1e21',
          font: { size: 12 }
        }
      }
    }
  };

  tempChart = new Chart(document.getElementById('graphTemp'), {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Température (°C)',
        data: tempData,
        borderColor: '#e53935',
        backgroundColor: 'rgba(229,57,53,0.15)',
        tension: 0.35,
        fill: true,
        pointRadius: 3,
        borderWidth: 2
      }]
    },
    options: {
      ...baseOptions,
      scales: {
        ...baseOptions.scales,
        y: {
          beginAtZero: true,
          suggestedMax: 50,
          ticks: { color: '#444' },
          grid: { color: '#e0e0e0' }
        }
      }
    }
  });

  humChart = new Chart(document.getElementById('graphHum'), {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Humidité (%)',
        data: humData,
        borderColor: '#1877f2',
        backgroundColor: 'rgba(24,119,242,0.15)',
        tension: 0.35,
        fill: true,
        pointRadius: 3,
        borderWidth: 2
      }]
    },
    options: {
      ...baseOptions,
      scales: {
        ...baseOptions.scales,
        y: {
          beginAtZero: true,
          suggestedMax: 100,
          ticks: { color: '#444' },
          grid: { color: '#e0e0e0' }
        }
      }
    }
  });

  gazChart = new Chart(document.getElementById('graphGaz'), {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Gaz (MQ-135)',
        data: gazData,
        borderColor: '#43a047',
        backgroundColor: 'rgba(67,160,71,0.15)',
        tension: 0.35,
        fill: true,
        pointRadius: 3,
        borderWidth: 2
      }]
    },
    options: {
      ...baseOptions,
      scales: {
        ...baseOptions.scales,
        y: {
          beginAtZero: true,
          suggestedMax: 500,
          ticks: { color: '#444' },
          grid: { color: '#e0e0e0' }
        }
      }
    }
  });
}

function chargerDonnees() {
  fetch('api/suivi')
    .then(response => {
      if (!response.ok) {
        throw new Error("Erreur réseau lors du chargement des données.");
      }
      return response.json();
    })
    .then(data => {
      const last = data.at(-1); // Dernier élément du tableau

      if (!last || !last.historique) {
        console.error("❌ Données manquantes dans le dernier objet.");
        return;
      }

      const tempVal = last.historique.temperature.at(-1);
      const humVal = last.historique.humidite.at(-1);
      const gazVal = last.historique.gaz.at(-1);

      document.getElementById('temp').textContent = `${tempVal ?? '--'} °C`;
      document.getElementById('hum').textContent = `${humVal ?? '--'} %`;
      document.getElementById('gaz').textContent = `${gazVal ?? '--'}`;

      const labels = last.historique.temperature.map((_, i) => i + 1);

      if (!tempChart || !humChart || !gazChart) {
        createCharts(labels, last.historique.temperature, last.historique.humidite, last.historique.gaz);
      } else {
        tempChart.data.labels = labels;
        humChart.data.labels = labels;
        gazChart.data.labels = labels;

        tempChart.data.datasets[0].data = last.historique.temperature;
        humChart.data.datasets[0].data = last.historique.humidite;
        gazChart.data.datasets[0].data = last.historique.gaz;

        tempChart.update();
        humChart.update();
        gazChart.update();
      }
    })

    .catch(error => {
      console.error("Erreur lors du chargement des données :", error);
    });
}

document.addEventListener("DOMContentLoaded", () => {
  chargerDonnees();
  setInterval(chargerDonnees, 5000);
});
