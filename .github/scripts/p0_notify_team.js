// Script to notify the team when a P0 issue is created.

const dryRun = (process.env.DRY_RUN || 'false').toString().toLowerCase() === 'true';

async function resolveIssueLabels(issue) {
    try {
        const p0Label = issue.labels.filter(label => label.name.toLowerCase() === 'p0');
        console.log(`Labels for Issue #${issue.number}:`, labels.map(l => l.name).join(', '));
        return p0Label;

    } catch (err) {
        console.log(`Failed to fetch labels for Issue #${issue.number}:`, err.message || err);
    }
}


// for an existing bot comment using our unique marker.
async function hasExistingBotComment(github, issue, owner, repo, marker) {
     try {
    const comments = await github.paginate(github.rest.issues.listComments, {
      owner,
      repo,
      issue_number: issue.number,
      per_page: 100,
    });
    return comments.find(c => c.body && c.body.includes(marker)) || false;
  } catch (err) {
    console.log(`Failed to list comments for PR #${issue.number}:`, err.message || err);
    return null; // Prevent duplicate comment if we cannot check
  }
}

async function postNotifyP0IssueComment(github, issue, owner, repo, marker) {
    const comment = `:rotating_light: Attention Team :rotating_light:
    @team-python-sdk/triage
    A new P0 issue has been created: #${issue.number} - ${issue.title}
    Please prioritize this issue accordingly.
    Best Regards,
    Automated Notification System
    ${marker}`;

    if (dryRun) {
        console.log(`DRY-RUN: Would comment on Issue #${issue.number} (${issue.html_url}) with body:\n---\n${comment}\n---`);
        return true;
    }
    
    try {
        await github.rest.issues.createComment({
            owner,
            repo,
            issue_number: issue.number,
            body: comment,
        });
        console.log(`Notified team about P0 issue #${issue.number}`);
        return true;
    } catch (commentErr) {
        console.log(`Failed to notify team about P0 issue #${issue.number}:`, commentErr.message || commentErr);
        return false;
    }
}


module.exports = async ({github, context}) => {
    const owner = context.repo.owner;
    const repo = context.repo.repo;
    const marker = '<!-- P0 Issue Notification -->';
    const issue = context.payload.issue;
    

    // Check for existing bot comment first
    const existingBotComment = await hasExistingBotComment(github, issue, owner, repo, marker);
    if (existingBotComment) {
        console.log(`A P0 notification comment already exists on Issue #${issue.number}. No duplicate comment posted.`);
        return;
    }
    // Check if the issue has the 'P0' label
    const labels = await resolveIssueLabels(issue);
    const hasP0Label = labels.some(label => label.name.toLowerCase() === 'p0');
    if (!hasP0Label) {
        console.log(`Issue #${issue.number} does not have the 'P0' label. No notification posted.`);
        return;
    }


    // Post the notification comment
    await postNotifyP0IssueComment(github, issue, owner, repo, marker);

    console.log("=== Summary ===");
    console.log(`Repository: ${owner}/${repo}`);
    console.log(`Issue Number: ${issue.number}`);
    console.log(`Issue Title: ${issue.title}`);
    console.log(`Labels: ${labels.join(', ')}`);
};
