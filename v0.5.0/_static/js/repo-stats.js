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

(function () {
  const devDocsName = "dev";
  const latestDocsName = "latest";
  const releaseVersionPattern = /^v\d+\.\d+\.\d+$/;
  const docsVersionSegmentPattern = /^(dev|latest|v\d+\.\d+\.\d+)$/;

  function safeDecode(value) {
    try {
      return decodeURIComponent(value);
    } catch (error) {
      return value;
    }
  }

  function unique(values) {
    return values.filter(function (value, index) {
      return value && values.indexOf(value) === index;
    });
  }

  function findDocsRootPath() {
    const segments = window.location.pathname.split("/");
    const versionIndex = segments.findIndex(function (segment) {
      return docsVersionSegmentPattern.test(safeDecode(segment));
    });
    if (versionIndex === -1) {
      return "";
    }
    return segments.slice(0, versionIndex).join("/") || "";
  }

  function manifestUrls() {
    const docsRootPath = findDocsRootPath();
    return unique([`${docsRootPath}/versions.json`, "/versions.json"]);
  }

  function normalizeManifestEntry(entry) {
    if (!entry || typeof entry.version !== "string" || !entry.version) {
      return null;
    }
    const aliases = Array.isArray(entry.aliases)
      ? entry.aliases.filter(function (alias) {
          return typeof alias === "string" && alias;
        })
      : [];
    return {
      version: entry.version,
      title: typeof entry.title === "string" && entry.title ? entry.title : entry.version,
      aliases,
    };
  }

  async function fetchVersionsManifest() {
    for (const url of manifestUrls()) {
      try {
        const response = await fetch(url, { cache: "no-store" });
        if (!response.ok) {
          continue;
        }
        const payload = await response.json();
        if (!Array.isArray(payload)) {
          continue;
        }
        return payload.map(normalizeManifestEntry).filter(Boolean);
      } catch (error) {
        continue;
      }
    }
    return [];
  }

  function getLatestReleaseEntry(entries) {
    return entries.find(function (entry) {
      return entry.aliases.includes(latestDocsName);
    });
  }

  function currentDocsLocation(entries) {
    const versions = new Set(
      entries.map(function (entry) {
        return entry.version;
      }),
    );
    const aliases = new Map();
    entries.forEach(function (entry) {
      entry.aliases.forEach(function (alias) {
        aliases.set(alias, entry.version);
      });
    });

    const segments = window.location.pathname.split("/");
    const versionIndex = segments.findIndex(function (segment) {
      const name = safeDecode(segment);
      return versions.has(name) || aliases.has(name);
    });
    if (versionIndex === -1) {
      return null;
    }

    const versionSegment = safeDecode(segments[versionIndex]);
    return {
      rootPath: segments.slice(0, versionIndex).join("/") || "",
      version: versionSegment,
      canonicalVersion: versions.has(versionSegment)
        ? versionSegment
        : aliases.get(versionSegment),
      pageSuffix: segments.slice(versionIndex + 1).join("/"),
    };
  }

  function versionUrl(location, versionName) {
    const pageSuffix = location.pageSuffix ? `/${location.pageSuffix}` : "/";
    return `${location.rootPath}/${encodeURIComponent(versionName)}${pageSuffix}${window.location.search}${window.location.hash}`;
  }

  function latestUrl(location) {
    return `${location.rootPath}/${latestDocsName}/`;
  }

  function appendSelectVersionGroup(select, label, entries, location) {
    if (!entries.length) {
      return;
    }

    const group = document.createElement("optgroup");
    group.label = label;
    entries.forEach(function (entry) {
      const option = document.createElement("option");
      option.value = versionUrl(location, entry.version);
      option.textContent = entry.title;
      option.selected = location.canonicalVersion === entry.version;
      group.appendChild(option);
    });
    select.appendChild(group);
  }

  function appendVersionGroup(container, label, entries, location) {
    if (!entries.length) {
      return;
    }

    const group = document.createElement("div");
    group.className = "docs-version-switcher-group";

    const title = document.createElement("span");
    title.className = "docs-version-switcher-group-title";
    title.textContent = label;

    const options = document.createElement("ul");
    options.className = "docs-version-switcher-options";
    entries.forEach(function (entry) {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.className = "docs-version-switcher-link";
      link.href = versionUrl(location, entry.version);
      link.textContent = entry.title;
      if (location.canonicalVersion === entry.version) {
        link.classList.add("is-active");
        link.setAttribute("aria-current", "page");
      }
      item.appendChild(link);
      options.appendChild(item);
    });
    group.append(title, options);
    container.appendChild(group);
  }

  function updateVersionSwitcher(entries, location) {
    const list = document.querySelector("#docs-version-switcher-list");
    const select = document.querySelector("#docs-version-switcher-select");
    if (!list && !select) {
      return;
    }

    const developmentVersions = entries.filter(function (entry) {
      return entry.version === devDocsName;
    });
    const releaseVersions = entries.filter(function (entry) {
      return releaseVersionPattern.test(entry.version);
    });

    if (list) {
      list.textContent = "";
      appendVersionGroup(list, "Development", developmentVersions, location);
      appendVersionGroup(list, "Releases", releaseVersions, location);
    }

    if (select) {
      select.textContent = "";
      appendSelectVersionGroup(
        select,
        "Development",
        developmentVersions,
        location,
      );
      appendSelectVersionGroup(select, "Releases", releaseVersions, location);
      select.onchange = function () {
        if (this.value) {
          window.location.assign(this.value);
        }
      };
    }

    const currentLabel = document.querySelector(".docs-version-switcher-current");
    if (!currentLabel) {
      return;
    }
    currentLabel.textContent =
      location.canonicalVersion === devDocsName
        ? "dev (main)"
        : location.canonicalVersion;
  }

  function removeVersionBanner() {
    document.querySelectorAll(".docs-version-banner").forEach(function (banner) {
      banner.remove();
    });
  }

  function getOrCreateVersionBanner() {
    const existingBanner = document.querySelector(".docs-version-banner");
    if (existingBanner) {
      return existingBanner;
    }

    const article = document.querySelector("article[role='main']");
    if (!article) {
      return null;
    }

    const banner = document.createElement("div");
    article.insertBefore(banner, article.firstChild);
    return banner;
  }

  function setVersionBanner(kind, title, href, label) {
    const banner = getOrCreateVersionBanner();
    if (!banner) {
      return;
    }

    banner.className = `docs-version-banner docs-version-banner--${kind}`;
    banner.textContent = "";

    const titleElement = document.createElement("p");
    titleElement.className = "docs-version-banner-title";
    titleElement.textContent = title;

    const link = document.createElement("a");
    link.className = "docs-version-banner-link";
    link.href = href;
    link.textContent = label;

    banner.append(titleElement, link);
  }

  function updateVersionBanner(entries, location) {
    const latestRelease = getLatestReleaseEntry(entries);
    if (!latestRelease) {
      return;
    }

    const latestLabel = latestRelease.title || latestRelease.version;
    const href = latestUrl(location);
    if (location.canonicalVersion === devDocsName) {
      setVersionBanner(
        "development",
        "You are reading the development documentation.",
        href,
        `View the latest stable release (${latestLabel})`,
      );
      return;
    }

    if (
      releaseVersionPattern.test(location.canonicalVersion)
      && location.canonicalVersion !== latestRelease.version
    ) {
      setVersionBanner(
        "outdated",
        "You are reading an older release of the documentation.",
        href,
        `View the latest stable release (${latestLabel})`,
      );
      return;
    }

    removeVersionBanner();
  }

  async function initDocsVersionNavigation() {
    if (
      !document.querySelector("#docs-version-switcher-list")
      && !document.querySelector("#docs-version-switcher-select")
      && !document.querySelector(".docs-version-banner")
    ) {
      return;
    }

    const entries = await fetchVersionsManifest();
    if (!entries.length) {
      return;
    }

    const location = currentDocsLocation(entries);
    if (!location || !location.canonicalVersion) {
      return;
    }

    updateVersionSwitcher(entries, location);
    updateVersionBanner(entries, location);
  }

  void initDocsVersionNavigation();
})();
