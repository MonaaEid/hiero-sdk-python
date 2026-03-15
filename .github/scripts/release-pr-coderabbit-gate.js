/**
 * Posts a single "@coderabbitai review" comment on release PRs.
 * Logic:
 * - Only runs for maintainer-authored PRs.
 * - Deduplicates via a hidden HTML marker.
 * - Injects a custom prompt from a markdown file.
 */

const fs = require("fs");
const path = require("path");

const MARKER = "<!-- coderabbit-release-gate: v1 -->";

function loadPrompt() {
  const promptPath = path.join(
    process.env.GITHUB_WORKSPACE || ".", 
    ".github/coderabbit/release-pr-prompt.md"
  );
  try {
    const content = fs.readFileSync(promptPath, "utf8").trim();
    if (!content) throw new Error("Release prompt file is empty");
    return content;
  } catch (error) {
    throw new Error(`Failed to load release prompt from ${promptPath}: ${error.message}`);
  }
}

async function commentAlreadyExists({ github, owner, repo, issue_number }) {
  try {
      // Pull a bounded number of recent comments to avoid pagination complexity.
      const { data } = await github.rest.issues.listComments({
      owner,
      repo,
      issue_number,
      per_page: 100,
      });
        return data.some((c) => typeof c.body === "string" && c.body.includes(MARKER));
      }
  catch (error) {
      console.error(`Error checking for existing comments: ${error.message}`);
      return false; // Fail open: allow posting if check fails
      }
}

function buildBody({ prompt, baseRef, headRef, baseLooksLikeTag }) {
  const lines = [
    "@coderabbitai review",
    "",
    MARKER,
    "",
    `## 🚀 Release Gate: ${baseRef} → ${headRef}`,
    "This PR has been identified as a **release candidate**. CodeRabbit will now perform an architectural audit based on the release-gate constraints.",
    "",
  ];

  if (!baseLooksLikeTag) {
    lines.push(
      "> [!WARNING]",
      "> The base branch (`" + baseRef + "`) does not match the standard release tag pattern (e.g., `release-v1.2.0`). The diff analysis might be broader than expected.",
      ""
    );
  }

  lines.push(
    "<details>",
    "<summary><b>View Release Review Instructions</b></summary>",
    "",
    prompt,
    "",
    "</details>",
  );
  return lines.join("\n");
}

module.exports = async ({ github, context }) => {
  try {
    const { owner, repo } = context.repo;
    const pr = context.payload.pull_request;

    if (!pr) return;

    // 1. Author Safety Check
    const assoc = pr.author_association;
    const isMaintainer = assoc === "MEMBER" || assoc === "OWNER";
    if (!isMaintainer) {
      console.log(`User association ${assoc} is not authorized for release-gate.`);
      return;
    }

    // 2. Prevent Duplicate Posting
    const issue_number = pr.number;
    if (await commentAlreadyExists({ github, owner, repo, issue_number })) {
      console.log("Marker comment found. Skipping post.");
      return;
    }

    // 3. Context Preparation
    const baseRef = pr.base?.ref || "";
    const headRef = pr.head?.ref || "";
    
    // Improved Regex: matches 'v1.0.0', '1.0.0', or 'release-v1.0.0'
    const baseLooksLikeTag = /^(release-)?v?\d+\.\d+\.\d+$/.test(baseRef);

    const prompt = loadPrompt();
    const body = buildBody({ prompt, baseRef, headRef, baseLooksLikeTag });

    // 4. Execution
    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number,
      body,
    });

    console.log(`Successfully triggered CodeRabbit gate for PR #${issue_number}`);
  } catch (error) {
    console.error(`Script failed: ${error.message}`);
  }
};
