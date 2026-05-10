// Color palette for charts
const chartColors = {
  primary: '#4F46E5',
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  info: '#3B82F6',
  light: '#E5E7EB',
  dark: '#1F2937',
  completed: '#86EFAC',
  inProgress: '#FCD34D',
  todo: '#93C5FD',
  backlog: '#D1D5DB'
};

let charts = {};

// Initialize all charts
async function initializeCharts() {
  try {
    // Load data from API
    const [
      taskDist,
      velocity,
      workload,
      priority,
      projectProgress,
      activeSprints
    ] = await Promise.all([
      fetch('/api/analytics/task-distribution').then(r => r.json()),
      fetch('/api/analytics/sprint-velocity').then(r => r.json()),
      fetch('/api/analytics/team-workload').then(r => r.json()),
      fetch('/api/analytics/priority-distribution').then(r => r.json()),
      fetch('/api/analytics/project-progress').then(r => r.json()),
      fetch('/api/analytics/active-sprints-summary').then(r => r.json())
    ]);

    // Update metrics cards
    updateMetricsCards(taskDist, projectProgress, activeSprints);

    // Initialize charts
    initSprintVelocityChart(velocity);
    initTaskDistributionChart(taskDist);
    initTeamWorkloadChart(workload);
    initPriorityDistributionChart(priority);
    initProjectProgressChart(projectProgress);
    renderActiveSprints(activeSprints);

  } catch (error) {
    console.error('Error loading analytics data:', error);
  }
}

// Update key metrics cards
function updateMetricsCards(taskDist, projectProgress, activeSprints) {
  const totalTasks = Object.values(taskDist).reduce((a, b) => a + b, 0);
  const completedTasks = taskDist.done || 0;
  const activeSprintCount = activeSprints.length;
  
  // Fetch team members count
  fetch('/api/users')
    .then(r => r.json())
    .then(users => {
      document.getElementById('team-members').textContent = users.length;
    });

  document.getElementById('total-tasks').textContent = totalTasks;
  document.getElementById('completed-tasks').textContent = completedTasks;
  document.getElementById('active-sprints').textContent = activeSprintCount;
}

// Sprint Velocity Chart - Line chart showing velocity trend
function initSprintVelocityChart(data) {
  if (!data.sprint_names || data.sprint_names.length === 0) {
    showNoDataMessage('velocityChart', 'No completed sprints yet');
    return;
  }

  const ctx = document.getElementById('velocityChart').getContext('2d');
  charts.velocity = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.sprint_names,
      datasets: [
        {
          label: 'Completed Points',
          data: data.velocities,
          borderColor: chartColors.success,
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          borderWidth: 3,
          fill: true,
          tension: 0.4,
          pointRadius: 6,
          pointBackgroundColor: chartColors.success,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointHoverRadius: 8
        },
        {
          label: 'Planned Points',
          data: data.planned_points,
          borderColor: chartColors.info,
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderWidth: 2,
          borderDash: [5, 5],
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointBackgroundColor: chartColors.info,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointHoverRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            usePointStyle: true,
            padding: 20,
            font: { size: 12, weight: '500' }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Story Points' }
        }
      }
    }
  });
}

// Task Distribution Chart - Pie chart showing status breakdown
function initTaskDistributionChart(data) {
  const ctx = document.getElementById('distributionChart').getContext('2d');
  const labels = ['Done', 'In Progress', 'Blocker', 'To Do', 'Backlog'];
  const values = [
    data.done || 0,
    data.in_progress || 0,
    data.blocker || 0,
    data.todo || 0,
    data.backlog || 0
  ];

  charts.distribution = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: [
          chartColors.success,
          chartColors.warning,
          chartColors.danger,
          chartColors.info,
          chartColors.light
        ],
        borderColor: '#fff',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            padding: 20,
            font: { size: 12 }
          }
        }
      }
    }
  });
}

// Team Workload Chart - Horizontal bar chart
function initTeamWorkloadChart(data) {
  if (!data || Object.keys(data).length === 0) {
    showNoDataMessage('workloadChart', 'No team workload data available');
    return;
  }

  const labels = Object.keys(data);
  const taskCounts = labels.map(name => data[name].task_count);
  const storyPoints = labels.map(name => data[name].story_points);

  const ctx = document.getElementById('workloadChart').getContext('2d');
  charts.workload = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Task Count',
          data: taskCounts,
          backgroundColor: chartColors.primary,
          borderColor: chartColors.primary,
          borderWidth: 1
        },
        {
          label: 'Story Points',
          data: storyPoints,
          backgroundColor: chartColors.info,
          borderColor: chartColors.info,
          borderWidth: 1
        }
      ]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          stacked: false
        }
      }
    }
  });
}

// Priority Distribution Chart - Bar chart
function initPriorityDistributionChart(data) {
  const ctx = document.getElementById('priorityChart').getContext('2d');
  const labels = ['Low', 'Medium', 'High'];
  const values = [
    data.low || 0,
    data.medium || 0,
    data.high || 0
  ];

  charts.priority = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Tasks',
        data: values,
        backgroundColor: [
          chartColors.info,
          chartColors.warning,
          chartColors.danger
        ],
        borderColor: [
          chartColors.info,
          chartColors.warning,
          chartColors.danger
        ],
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      indexAxis: 'x',
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}

// Project Progress Chart - Horizontal bar chart
function initProjectProgressChart(data) {
  if (!data || data.length === 0) {
    showNoDataMessage('projectProgressChart', 'No projects available');
    return;
  }

  const labels = data.map(p => p.name);
  const progress = data.map(p => p.progress);

  const ctx = document.getElementById('projectProgressChart').getContext('2d');
  charts.projectProgress = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Completion %',
        data: progress,
        backgroundColor: progress.map(p => {
          if (p >= 80) return chartColors.success;
          if (p >= 50) return chartColors.warning;
          return chartColors.danger;
        }),
        borderRadius: 4,
        borderSkipped: false
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: function(value) {
              return value + '%';
            }
          }
        }
      }
    }
  });
}

// Render Active Sprints Summary
function renderActiveSprints(sprints) {
  const container = document.getElementById('activeSprints');
  container.replaceChildren(); // Clear existing content

  if (!sprints || sprints.length === 0) {
    const emptyMsg = document.createElement('p');
    emptyMsg.className = 'text-muted text-center py-4';
    emptyMsg.textContent = 'No active sprints at the moment';
    container.appendChild(emptyMsg);
    return;
  }

  sprints.forEach(sprint => {
    const card = document.createElement('div');
    card.className = 'sprint-summary-card';
    
    const header = document.createElement('div');
    header.className = 'sprint-header';
    
    const title = document.createElement('h4');
    title.textContent = sprint.name;
    
    const badge = document.createElement('span');
    badge.className = 'sprint-progress-badge';
    badge.textContent = sprint.completion_percent + '%';
    
    header.appendChild(title);
    header.appendChild(badge);
    
    const metrics = document.createElement('div');
    metrics.className = 'sprint-metrics';
    
    // Tasks Completed metric
    const tasksMetric = document.createElement('div');
    tasksMetric.className = 'metric';
    
    const tasksLabel = document.createElement('div');
    tasksLabel.className = 'metric-label';
    tasksLabel.textContent = 'Tasks Completed';
    
    const tasksValue = document.createElement('div');
    tasksValue.className = 'metric-value';
    tasksValue.textContent = sprint.completed_tasks + ' / ' + sprint.task_count;
    
    const progress = document.createElement('div');
    progress.className = 'progress';
    progress.style.height = '6px';
    
    const progressBar = document.createElement('div');
    progressBar.className = 'progress-bar bg-success';
    progressBar.setAttribute('role', 'progressbar');
    progressBar.style.width = sprint.completion_percent + '%';
    progressBar.setAttribute('aria-valuenow', sprint.completion_percent);
    progressBar.setAttribute('aria-valuemin', '0');
    progressBar.setAttribute('aria-valuemax', '100');
    
    progress.appendChild(progressBar);
    tasksMetric.appendChild(tasksLabel);
    tasksMetric.appendChild(tasksValue);
    tasksMetric.appendChild(progress);
    
    // Story Points metric
    const pointsMetric = document.createElement('div');
    pointsMetric.className = 'metric';
    
    const pointsLabel = document.createElement('div');
    pointsLabel.className = 'metric-label';
    pointsLabel.textContent = 'Story Points';
    
    const pointsValue = document.createElement('div');
    pointsValue.className = 'metric-value';
    pointsValue.textContent = sprint.completed_points + ' / ' + sprint.total_points + ' pts';
    
    pointsMetric.appendChild(pointsLabel);
    pointsMetric.appendChild(pointsValue);
    
    metrics.appendChild(tasksMetric);
    metrics.appendChild(pointsMetric);
    
    card.appendChild(header);
    card.appendChild(metrics);
    container.appendChild(card);
  });
}

// Helper function to show "no data" message
function showNoDataMessage(elementId, message) {
  const element = document.getElementById(elementId);
  const parent = element.parentElement;

  const emptyMsg = document.createElement('p');
  emptyMsg.className = 'text-muted text-center py-5';
  emptyMsg.textContent = message;

  parent.replaceChildren(emptyMsg);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initializeCharts);
