/**
 * Posts a single "@coderabbit review" comment on release PRs, embedding the
 * release review prompt. Designed to run with:
 * - permissions: contents: read, pull-requests: write
 *
 * Safety:
 * - Only runs for maintainer-authored PRs (MEMBER/OWNER)
 * - Dedupe via hidden marker comment
 */

const fs = require("fs");
const path = require("path");

const MARKER = "<!-- coderabbit-release-gate: v1 -->";


function loadPrompt() {
  const promptPath = path.join(process.env.GITHUB_WORKSPACE || ".", ".github/coderabbit/release-pr-prompt.md");
  try{
    const content = fs.readFileSync(promptPath, "utf8").trim();
    if (!content) {
      throw new Error("Release prompt file is empty");
      }
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


function buildBody({ prompt, baseRef, headRef }) {
  // Keep it human-friendly but compact; instructions are collapsible.
  return [
    "@coderabbit review",
    "",
    MARKER,
    "",
    `This is a **release-gate** review request for diff **${baseRef} → ${headRef}**.`,
    "",
    "<details>",
    "<summary>CodeRabbit release review instructions</summary>",
    "",
    prompt,
    "",
    "</details>",
  ].join("\n");
}

module.exports = async ({ github, context }) => {
  try {
    const owner = context.repo.owner;
    const repo = context.repo.repo;
    const pr = context.payload.pull_request;

    if (!pr) {
      console.log("No pull_request payload; exiting.");
      return;
    }

    // Safety: only maintainers
    const assoc = pr.author_association;
    if (!(assoc === "MEMBER" || assoc === "OWNER")) {
      console.log(`author_association=${assoc}; skipping.`);
      return;
    }

    const title = pr.title || "";
    if (!title.toLowerCase().startsWith("chore: release v")) {
      console.log("Not a release PR title; skipping.");
      return;
    }

    const baseRef = pr.base?.ref || "";
    const headRef = pr.head?.ref || "";

    // Optional sanity check: base should look like a tag. If it doesn't, still comment but warn.
    const baseLooksLikeTag = baseRef.startsWith("v") && /\d+\.\d+\.\d+/.test(baseRef);

    const issue_number = pr.number;
    if (await commentAlreadyExists({ github, owner, repo, issue_number })) {
      console.log("Marker comment already exists; not posting again.");
      return;
    }

    const prompt = loadPrompt();

    const body = buildBody({ prompt, baseRef, headRef }) +
      (baseLooksLikeTag ? "" : "\n\n⚠️ Note: base ref does not look like a release tag. For full release diff, set base to the previous tag (e.g. v0.1.10).");

    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number,
      body,
    });

    console.log("Posted CodeRabbit release-gate comment.");
  } catch (error) {
    console.error(`Error in release PR coderabbit gate: ${error.message}`);
    // Fail silently; this is a non-critical enhancement.
  }
};
