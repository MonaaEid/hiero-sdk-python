// Script to notify the team when a P0 issue is created.

const dryRun = (process.env.DRY_RUN || 'false').toString().toLowerCase() === 'true';

async function resolveIssueLabels(github, ownerName, repoName, issueObj) {
    try {
      if (Array.isArray(issueObj.labels) && issueObj.labels.length > 0) {
        console.log(`Using labels from payload for Issue #${issueObj.number}`);
        return issueObj.labels;
      }

      console.log(`Fetching labels from API for Issue #${issueObj.number}`);
      const labels = await github.paginate(github.rest.issues.listLabelsOnIssue, {
        owner: ownerName,
        repo: repoName,
        issue_number: issueObj.number,
        per_page: 100,
      });

      return Array.isArray(labels) ? labels : [];
    } catch (err) {
      console.log(`Failed to resolve labels for Issue #${issueObj.number}:`, err.message || err);
      // Return empty array so callers can operate safely.
      return [];
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
    
    // Early return if no issue in payload (e.g., scheduled or manual runs without issue context)
    if (!issue || !issue.number) {
        console.log('No issue found in payload. Skipping notification.');
        return;
    }

    // Check for existing bot comment first
    const existingBotComment = await hasExistingBotComment(github, issue, owner, repo, marker);
    if (existingBotComment) {
        console.log(`A P0 notification comment already exists on Issue #${issue.number}. No duplicate comment posted.`);
        return;
    }
    // Check if the issue has the 'P0' label
    // const labels = await resolveIssueLabels(issue);
    // const hasP0Label = labels.some(label => label.name.toLowerCase() === 'p0');
    // if (!hasP0Label) {
    //     console.log(`Issue #${issue.number} does not have the 'P0' label. No notification posted.`);
    //     return;
    // }
    const labels = await resolveIssueLabels(github, owner, repo, issue);
    const hasP0Label = Array.isArray(labels) && labels.some(label => (label && label.name && label.name.toLowerCase()) === 'p0');

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
