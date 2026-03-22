(function () {
  const releaseNotesContainers = document.querySelectorAll(".js-release-notes");
  if (!releaseNotesContainers.length) {
    return;
  }

  const markdownRenderer = window.snarkdown;
  const dateFormatter = new Intl.DateTimeFormat("en", { dateStyle: "long" });
  const pageSize = 100;
  const maxPages = 10;
  const plainUrlPattern = /https?:\/\/[^\s<]+/g;
  const generatedReleaseNotesCommentPattern =
    /^\s*<!--\s*Release notes generated using configuration in \.github\/release\.yml(?: at .*?)?\s*-->\s*$/i;

  function getCacheKey(user, repo) {
    return `release-notes:github:${user}/${repo}`;
  }

  function escapeHtml(value) {
    return value.replace(/[&<>]/g, function (character) {
      if (character === "&") {
        return "&amp;";
      }
      if (character === "<") {
        return "&lt;";
      }
      return "&gt;";
    });
  }

  function isSafeUrl(url) {
    try {
      const parsed = new URL(url, window.location.href);
      return ["http:", "https:", "mailto:"].includes(parsed.protocol);
    } catch (error) {
      return false;
    }
  }

  function isExternalUrl(url) {
    try {
      return new URL(url, window.location.href).origin !== window.location.origin;
    } catch (error) {
      return false;
    }
  }

  function createSafeLink(url, label) {
    if (!isSafeUrl(url)) {
      return document.createTextNode(label);
    }

    const link = document.createElement("a");
    link.href = url;
    link.textContent = label;

    if (isExternalUrl(url)) {
      link.rel = "noreferrer noopener";
      link.target = "_blank";
    }

    return link;
  }

  function linkifyPlainTextUrls(root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        const parent = node.parentElement;
        if (!parent || !node.textContent || !plainUrlPattern.test(node.textContent)) {
          plainUrlPattern.lastIndex = 0;
          return NodeFilter.FILTER_REJECT;
        }

        plainUrlPattern.lastIndex = 0;
        if (parent.closest("a, code, pre, samp, kbd, script, style, textarea")) {
          return NodeFilter.FILTER_REJECT;
        }

        return NodeFilter.FILTER_ACCEPT;
      },
    });

    const textNodes = [];
    while (walker.nextNode()) {
      textNodes.push(walker.currentNode);
    }

    textNodes.forEach(function (textNode) {
      const text = textNode.textContent || "";
      plainUrlPattern.lastIndex = 0;

      let match = plainUrlPattern.exec(text);
      if (!match) {
        return;
      }

      const fragment = document.createDocumentFragment();
      let currentIndex = 0;

      while (match) {
        let url = match[0];
        let trailingPunctuation = "";

        while (/[),.;!?]$/.test(url)) {
          trailingPunctuation = url.slice(-1) + trailingPunctuation;
          url = url.slice(0, -1);
        }

        if (match.index > currentIndex) {
          fragment.appendChild(
            document.createTextNode(text.slice(currentIndex, match.index)),
          );
        }

        fragment.appendChild(createSafeLink(url, url));

        if (trailingPunctuation) {
          fragment.appendChild(document.createTextNode(trailingPunctuation));
        }

        currentIndex = match.index + match[0].length;
        match = plainUrlPattern.exec(text);
      }

      if (currentIndex < text.length) {
        fragment.appendChild(document.createTextNode(text.slice(currentIndex)));
      }

      textNode.replaceWith(fragment);
    });
  }

  function sanitizeRenderedContent(root) {
    linkifyPlainTextUrls(root);

    for (const link of root.querySelectorAll("a")) {
      const href = link.getAttribute("href");
      if (!href || !isSafeUrl(href)) {
        link.replaceWith(document.createTextNode(link.textContent || ""));
        continue;
      }

      if (isExternalUrl(href)) {
        link.rel = "noreferrer noopener";
        link.target = "_blank";
      }
    }

    for (const image of root.querySelectorAll("img")) {
      image.loading = "lazy";
      image.decoding = "async";
    }
  }

  function readCache(cacheKey) {
    try {
      const cachedValue = sessionStorage.getItem(cacheKey);
      if (!cachedValue) {
        return null;
      }
      const payload = JSON.parse(cachedValue);
      return Array.isArray(payload) ? payload : null;
    } catch (error) {
      return null;
    }
  }

  function writeCache(cacheKey, releases) {
    try {
      sessionStorage.setItem(cacheKey, JSON.stringify(releases));
    } catch (error) {
      return;
    }
  }

  function setStatus(container, message, state) {
    const status = container.querySelector(".js-release-notes-status");
    if (!status) {
      return;
    }
    status.hidden = false;
    status.dataset.state = state;
    status.textContent = message;
  }

  function hideStatus(container) {
    const status = container.querySelector(".js-release-notes-status");
    if (!status) {
      return;
    }
    status.hidden = true;
  }

  function getHeadingLabel(heading) {
    const clone = heading.cloneNode(true);
    clone.querySelectorAll(".headerlink").forEach(function (link) {
      link.remove();
    });
    return clone.textContent.trim();
  }

  function addHeadingPermalink(heading) {
    if (!heading.id || heading.querySelector(".headerlink")) {
      return;
    }

    const permalink = document.createElement("a");
    permalink.className = "headerlink";
    permalink.href = `#${heading.id}`;
    permalink.title = "Link to this heading";
    permalink.setAttribute("aria-label", "Link to this heading");
    permalink.textContent = "¶";
    heading.appendChild(permalink);
  }

  function normalizeReleaseBody(body) {
    if (typeof body !== "string" || !body.trim()) {
      return "_No release notes provided._";
    }

    const normalizedBody = body
      .split(/\r?\n/)
      .filter(function (line) {
        return !generatedReleaseNotesCommentPattern.test(line);
      })
      .join("\n")
      .trim();

    return normalizedBody || "_No release notes provided._";
  }

  function renderMarkdown(body) {
    if (typeof markdownRenderer !== "function") {
      return "<p>Release notes could not be rendered in the browser.</p>";
    }

    const source = normalizeReleaseBody(body);
    return markdownRenderer(escapeHtml(source));
  }

  function demoteReleaseBodyHeadings(root) {
    const headings = Array.from(
      root.querySelectorAll("h1, h2, h3, h4, h5, h6"),
    );

    headings.forEach(function (heading) {
      const currentLevel = Number(heading.tagName.slice(1));
      const nextLevel = Math.min(currentLevel + 1, 6);
      if (nextLevel === currentLevel) {
        return;
      }

      const replacement = document.createElement(`h${nextLevel}`);
      heading.getAttributeNames().forEach(function (attributeName) {
        replacement.setAttribute(
          attributeName,
          heading.getAttribute(attributeName) || "",
        );
      });

      while (heading.firstChild) {
        replacement.appendChild(heading.firstChild);
      }

      heading.replaceWith(replacement);
    });
  }

  function assignReleaseBodyHeadingIds(root, prefix) {
    const assignedIds = new Set([prefix]);
    const headings = Array.from(root.querySelectorAll("h1, h2, h3, h4, h5, h6"));

    headings.forEach(function (heading, index) {
      if (heading.id) {
        assignedIds.add(heading.id);
        return;
      }

      const headingLabel = getHeadingLabel(heading);
      const baseId = `${prefix}-${slugify(headingLabel, `section-${index}`)}`;
      let headingId = baseId;
      let duplicateIndex = 2;

      while (assignedIds.has(headingId) || document.getElementById(headingId)) {
        headingId = `${baseId}-${duplicateIndex}`;
        duplicateIndex += 1;
      }

      heading.id = headingId;
      assignedIds.add(headingId);
    });
  }

  function addPermalinksToHeadings(root) {
    root.querySelectorAll("h1, h2, h3, h4, h5, h6").forEach(function (heading) {
      addHeadingPermalink(heading);
    });
  }

  function ensurePageTocTree() {
    const tocDrawer = document.querySelector(".toc-drawer");
    if (!tocDrawer) {
      return null;
    }

    let tocTree = tocDrawer.querySelector(".toc-tree");
    if (tocTree) {
      return tocTree;
    }

    const sticky = document.createElement("div");
    sticky.className = "toc-sticky toc-scroll";

    const titleContainer = document.createElement("div");
    titleContainer.className = "toc-title-container";

    const title = document.createElement("span");
    title.className = "toc-title";
    title.textContent = "On this page";
    titleContainer.appendChild(title);

    const treeContainer = document.createElement("div");
    treeContainer.className = "toc-tree-container";

    tocTree = document.createElement("div");
    tocTree.className = "toc-tree";
    treeContainer.appendChild(tocTree);

    sticky.appendChild(titleContainer);
    sticky.appendChild(treeContainer);
    tocDrawer.replaceChildren(sticky);

    return tocTree;
  }

  function setTocVisibility(isVisible) {
    document.querySelectorAll(
      ".toc-header-icon, .toc-content-icon, .toc-drawer",
    ).forEach(function (element) {
      element.classList.toggle("no-toc", !isVisible);
    });
  }

  function updatePageToc(container) {
    const tocTree = ensurePageTocTree();
    if (!tocTree) {
      return;
    }

    const releaseHeadings = Array.from(
      container.querySelectorAll(".release-notes-title[id]"),
    );
    if (!releaseHeadings.length) {
      tocTree.replaceChildren();
      setTocVisibility(false);
      return;
    }

    const pageHeading = document.querySelector("article[role='main'] h1");
    const rootList = document.createElement("ul");
    const rootItem = document.createElement("li");
    const rootLink = document.createElement("a");
    rootLink.className = "reference internal";
    rootLink.href = pageHeading?.id ? `#${pageHeading.id}` : "#";
    rootLink.textContent = pageHeading
      ? getHeadingLabel(pageHeading)
      : "Release Notes";
    rootItem.appendChild(rootLink);

    const nestedList = document.createElement("ul");
    releaseHeadings.forEach(function (heading) {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.className = "reference internal";
      link.href = `#${heading.id}`;
      link.textContent = getHeadingLabel(heading);
      item.appendChild(link);
      nestedList.appendChild(item);
    });

    rootItem.appendChild(nestedList);
    rootList.appendChild(rootItem);
    tocTree.replaceChildren(rootList);
    setTocVisibility(true);
  }

  function scrollToCurrentHash() {
    if (!window.location.hash) {
      return;
    }

    let targetId = window.location.hash.slice(1);
    try {
      targetId = decodeURIComponent(targetId);
    } catch (error) {
      return;
    }

    const target = document.getElementById(targetId);
    if (!target) {
      return;
    }

    target.scrollIntoView();
  }

  function slugify(value, fallback) {
    const slug = String(value || "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return slug || fallback;
  }

  function createReleaseArticle(release, index) {
    const article = document.createElement("article");
    article.className = "release-notes-entry";

    const header = document.createElement("div");
    header.className = "release-notes-header";

    const heading = document.createElement("h2");
    heading.className = "release-notes-title";
    heading.id = `release-${slugify(
      release.tag_name || release.name,
      `entry-${index}`,
    )}`;
    article.setAttribute("aria-labelledby", heading.id);
    heading.textContent = release.name && release.name !== release.tag_name
      ? release.name
      : release.tag_name;
    addHeadingPermalink(heading);

    const publishedDate = release.published_at || release.created_at;
    header.appendChild(heading);

    if (publishedDate) {
      const meta = document.createElement("div");
      meta.className = "release-notes-meta";

      const date = document.createElement("span");
      date.textContent = dateFormatter.format(new Date(publishedDate));
      meta.appendChild(date);

      header.appendChild(meta);
    }

    const body = document.createElement("div");
    body.className = "release-notes-body";
    body.innerHTML = renderMarkdown(release.body);
    demoteReleaseBodyHeadings(body);
    assignReleaseBodyHeadingIds(body, heading.id);
    addPermalinksToHeadings(body);
    sanitizeRenderedContent(body);

    article.appendChild(header);
    article.appendChild(body);

    return article;
  }

  function renderReleases(container, releases) {
    const list = container.querySelector(".js-release-notes-list");
    if (!list) {
      return;
    }

    list.replaceChildren();

    if (!releases.length) {
      list.hidden = true;
      setStatus(
        container,
        "No published stable releases are available yet. Browse GitHub Releases for upcoming drafts.",
        "empty",
      );
      return;
    }

    releases.forEach(function (release, index) {
      list.appendChild(createReleaseArticle(release, index));
    });

    list.hidden = false;
    hideStatus(container);
    updatePageToc(container);
    scrollToCurrentHash();
  }

  async function fetchAllReleases(user, repo) {
    const releases = [];

    for (let page = 1; page <= maxPages; page += 1) {
      const response = await fetch(
        `https://api.github.com/repos/${encodeURIComponent(user)}/${encodeURIComponent(repo)}/releases?per_page=${pageSize}&page=${page}`,
        {
          headers: {
            Accept: "application/vnd.github+json",
          },
        },
      );

      if (!response.ok) {
        throw new Error(`GitHub API returned ${response.status}`);
      }

      const payload = await response.json();
      if (!Array.isArray(payload)) {
        throw new Error("GitHub API returned an unexpected response");
      }

      releases.push(...payload);

      if (payload.length < pageSize) {
        break;
      }
    }

    return releases.filter(function (release) {
      return !release?.draft && !release?.prerelease;
    });
  }

  async function initReleaseNotes(container) {
    const user = container.dataset.user;
    const repo = container.dataset.repo;
    if (!user || !repo) {
      setStatus(
        container,
        "Release notes are not configured for this page yet.",
        "error",
      );
      return;
    }

    if (typeof markdownRenderer !== "function") {
      setStatus(
        container,
        "Release notes could not be rendered in the browser. Please use GitHub Releases instead.",
        "error",
      );
      return;
    }

    const cacheKey = getCacheKey(user, repo);
    const cachedReleases = readCache(cacheKey);
    if (cachedReleases) {
      renderReleases(container, cachedReleases);
      return;
    }

    setStatus(container, "Loading published releases from GitHub...", "loading");

    try {
      const releases = await fetchAllReleases(user, repo);
      writeCache(cacheKey, releases);
      renderReleases(container, releases);
    } catch (error) {
      setStatus(
        container,
        "Release notes are temporarily unavailable here. Please use GitHub Releases for the latest details.",
        "error",
      );
    }
  }

  releaseNotesContainers.forEach(function (container) {
    void initReleaseNotes(container);
  });
})();
