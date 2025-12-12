// Script to notify the team when a P0 issue is created.

const dryRun = (process.env.DRY_RUN || 'false').toString().toLowerCase() === 'true';


// Look for an existing bot comment using our unique marker.
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
    
    // Only proceed if the issue is labeled as P0
    const issue = context.payload.issue;
    const labels = (issue.labels || []).map(label => label.name);
    if (labels.includes('P0')) {
        await postNotifyP0IssueComment(github, issue, owner, repo, marker);
    } else {
        console.log(`Issue #${issue.number} is not labeled as P0. No action taken.`);
    }

    const existingBotComment = await hasExistingBotComment(github, issue, owner, repo, marker);
    if (existingBotComment) {
        console.log(`A P0 notification comment already exists on Issue #${issue.number}. No duplicate comment posted.`);
        return;
    }

      console.log("=== Summary ===");
        console.log(`Repository: ${owner}/${repo}`);
        console.log(`Issue Number: ${issue.number}`);
        console.log(`Issue Title: ${issue.title}`);
        console.log(`Labels: ${labels.join(', ')}`);
    };
