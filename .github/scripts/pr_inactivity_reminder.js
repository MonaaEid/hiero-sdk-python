module.exports = ({github, context}) => {
const inactivityThresholdDays = 10;
const cutoff = new Date(Date.now() - inactivityThresholdDays * 24 * 60 * 60 * 1000);
const owner = context.repo.owner;
const repo = context.repo.repo;
const labelName = 'no-pr-activity';

let labeledCount = 0;
let skippedCount = 0;

// Ensure label exists once up front
async function ensureLabel() {
    try {
    await github.rest.issues.getLabel({ owner, repo, name: labelName });
    } catch (err) {
    if (err.status === 404) {
        await github.rest.issues.createLabel({
        owner,
        repo,
        name: labelName,
        color: 'EFEFEF',
        description: 'Pull request has had no development activity (commits)',
        });
        console.log(`Created label '${labelName}'`);
    }
    }
}
await ensureLabel();

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
    console.log(`Failed to fetch commits for PR #${pr.number}:`, err.message || err);
    lastCommitDate = new Date(pr.updated_at);
    }

    if (lastCommitDate > cutoff) {
    console.log(`PR #${pr.number} has recent commit on ${lastCommitDate.toISOString()} - skipping`);
    continue;
    }

    const hasLabel = pr.labels && pr.labels.some(l => l.name === labelName);
    if (hasLabel) {
    skippedCount++;
    console.log(`PR #${pr.number} already has label '${labelName}' - skipping`);
    continue;
    }

    try {
    await github.rest.issues.addLabels({
        owner,
        repo,
        issue_number: pr.number,
        labels: [labelName],
    });
    labeledCount++;
    console.log(`Added label '${labelName}' to PR #${pr.number}`);
    } catch (err) {
    console.log(`Failed to add label for PR #${pr.number}:`, err);
    continue;
    }

    const comment = `Hi @${pr.user.login},\n\nThis pull request has had no commit activity for ${daysBefore} days. Are you still working on the issue? If you are still working on it, please push a commit or let us know your status.\n\nFrom the Python SDK Team`;

    try {
    await github.rest.issues.createComment({
        owner,
        repo,
        issue_number: pr.number,
        body: comment,
    });
    console.log(`Commented PR #${pr.number} (${pr.html_url})`);
    } catch (commentErr) {
    console.log(`Failed to comment on PR #${pr.number}:`, commentErr);
    }
}

console.log("=== Summary ===");
console.log(`PRs labeled: ${labeledCount}`);
console.log(`PRs skipped (already labeled): ${skippedCount}`);
}
