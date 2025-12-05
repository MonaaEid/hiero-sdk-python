module.exports = async ({github, context}) => {
const inactivityThresholdDays = 1;
const cutoff = new Date(Date.now() - inactivityThresholdDays * 24 * 60 * 60 * 1000);
const owner = context.repo.owner;
const repo = context.repo.repo;

// Unique marker so we can find the bot's own comment later.
const marker = '<!-- pr-inactivity-bot-marker -->';

let commentedCount = 0;
let skippedCount = 0;

const prs = await github.paginate(github.rest.pulls.list, {
  owner,
  repo,
  state: 'open',
  per_page: 100,
});

for (const pr of prs) {
  let lastCommitDate;
  try {
  const commits = await github.rest.pulls.listCommits({
      owner,
      repo,
      pull_number: pr.number,
      per_page: 1,
  });
  const commit = commits.data[0]?.commit;
  lastCommitDate = new Date(
  commit?.author?.date ||
  commit?.committer?.date ||
  pr.updated_at
      );
  } catch (err) {
    console.log(`Failed to fetch commit for PR #${pr.number}:`, err.message || err);
    lastCommitDate = new Date(pr.updated_at);
  }

  if (lastCommitDate > cutoff) {
    console.log(`PR #${pr.number} has recent commit on ${lastCommitDate.toISOString()} - skipping`);
    continue;
  }

  // Look for an existing bot comment using our unique marker.
  let existingBotComment = null;
  try {
    const comments = await github.paginate(github.rest.issues.listComments, {
      owner,
      repo,
      issue_number: pr.number,
      per_page: 100,
    });

    existingBotComment = comments.find(c => c.body && c.body.includes(marker));
  } catch (err) {
    console.log(`Failed to list comments for PR #${pr.number}:`, err.message || err);
    // If comments can't be fetched, skip to avoid duplicates/spam.
    continue;
  }

  if (existingBotComment) {
    skippedCount++;
    console.log(`PR #${pr.number} already has an inactivity comment (id: ${existingBotComment.id}) - skipping`);
    continue;
  }

  const comment = `${marker}
   Hi @${pr.user.login},\n\nThis pull request has had no development activity for ${inactivityThresholdDays} days. Are you still working on the issue? Reach out on discord or join our office hours if you need assistance.\n\nFrom the Python SDK Team`;

  try {
    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number: pr.number,
      body: comment,
    });
    commentedCount++;
    console.log(`Commented on PR #${pr.number} (${pr.html_url})`);
  } catch (commentErr) {
    console.log(`Failed to comment on PR #${pr.number}:`, commentErr);
  }
}

console.log("=== Summary ===");
console.log(`PRs commented: ${commentedCount}`);
console.log(`PRs skipped (existing comment present): ${skippedCount}`);
}
