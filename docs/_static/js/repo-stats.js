(function () {
  const repoStatsCard = document.querySelector(".js-repo-stats");
  if (!repoStatsCard) {
    return;
  }

  const user = repoStatsCard.dataset.user;
  const repo = repoStatsCard.dataset.repo;
  const type = repoStatsCard.dataset.type;
  if (!user || !repo || type !== "github") {
    return;
  }

  const formatter = new Intl.NumberFormat();
  const cacheKey = `repo-stats:${type}:${user}/${repo}`;

  function updateCount(selector, value) {
    const element = repoStatsCard.querySelector(selector);
    if (!element || typeof value !== "number" || Number.isNaN(value)) {
      return;
    }
    element.textContent = formatter.format(value);
  }

  function updateRepoStats(stats) {
    if (!stats) {
      return;
    }
    updateCount(".js-repo-stars", stats.stars);
    updateCount(".js-repo-forks", stats.forks);
  }

  function readCache() {
    try {
      const cached = sessionStorage.getItem(cacheKey);
      if (!cached) {
        return null;
      }
      const parsed = JSON.parse(cached);
      if (
        typeof parsed?.stars === "number"
        && typeof parsed?.forks === "number"
      ) {
        return parsed;
      }
    } catch (error) {
      return null;
    }
    return null;
  }

  function writeCache(stats) {
    try {
      sessionStorage.setItem(cacheKey, JSON.stringify(stats));
    } catch (error) {
      return;
    }
  }

  async function fetchGitHubRepoStats() {
    try {
      const response = await fetch(
        `https://api.github.com/repos/${encodeURIComponent(user)}/${encodeURIComponent(repo)}`,
      );
      if (!response.ok) {
        return null;
      }
      const payload = await response.json();
      if (
        typeof payload?.stargazers_count !== "number"
        || typeof payload?.forks_count !== "number"
      ) {
        return null;
      }
      return {
        stars: payload.stargazers_count,
        forks: payload.forks_count,
      };
    } catch (error) {
      return null;
    }
  }

  async function initRepoStats() {
    const cached = readCache();
    if (cached) {
      updateRepoStats(cached);
      return;
    }

    const stats = await fetchGitHubRepoStats();
    if (!stats) {
      return;
    }

    updateRepoStats(stats);
    writeCache(stats);
  }

  void initRepoStats();
})();
