// Script to notify the team when a P0 issue is created. 

module.exports = async ({ github, context, customPayload = null }) => {
  const owner = context.repo && context.repo.owner;
  const repo = context.repo && context.repo. repo;
  const marker = '<!-- P0 Issue Notification -->';
  
  // Use custom payload if provided (for testing), otherwise use the real event payload
  const payload = customPayload || context.payload;
  const issue = payload && payload.issue;

  // Compute dry-run at execution time so we pick up the runtime env value. 
  const dryRun = (process.env.DRY_RUN || 'false').toString().toLowerCase() === 'true';

  console.log(`Running in ${dryRun ? 'DRY-RUN' : 'LIVE'} mode`);
  if (customPayload) {
    console.log('⚠️  Using CUSTOM PAYLOAD for testing');
  }

  // Early return if no issue in payload
  if (!issue || typeof issue. number === 'undefined') {
    console.log('No issue found in the event payload. Nothing to do.');
    return;
  }

  // Fast-fail for "labeled" events that aren't the P0 label
  const action = payload && payload.action;
  if (action === 'labeled') {
    const label = payload. label;
    if (! label || (label.name || '').toLowerCase() !== 'p0') {
      console.log(`Issue #${issue.number} was labeled with '${label ? label. name : 'unknown'}' — not 'p0'. Exiting.`);
      return;
    }
    // If we get here, the label event is specifically the P0 label.
  }

  // Helper: resolve labels for an issue — prefer payload labels, otherwise fetch from the API.
  async function resolveIssueLabels(githubClient, ownerName, repoName, issueObj) {
    try {
      if (Array.isArray(issueObj.labels) && issueObj.labels.length > 0) {
        console.log(`Using labels from payload for Issue #${issueObj.number}`);
        return issueObj.labels;
      }

      console. log(`Fetching labels from API for Issue #${issueObj. number}`);
      const labels = await githubClient.paginate(githubClient.rest.issues. listLabelsOnIssue, {
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

  // Check for an existing bot comment using our unique marker. 
  async function hasExistingBotComment(githubClient, ownerName, repoName, issueObj, markerText) {
    try {
      const comments = await githubClient.paginate(githubClient.rest. issues.listComments, {
        owner: ownerName,
        repo: repoName,
        issue_number: issueObj.number,
        per_page: 100,
      });

      const found = comments.find(c => c.body && c. body.includes(markerText));
      return !!found;
    } catch (err) {
      console.log(`Failed to list comments for Issue #${issueObj.number}:`, err.message || err);
      // Be conservative: if we cannot check comments, avoid posting to prevent duplicates.
      return true;
    }
  }

  async function postNotifyP0IssueComment(githubClient, ownerName, repoName, issueObj, markerText) {
    const comment = `:rotating_light: Attention Team :rotating_light: 
@team-python-sdk/triage

A new P0 issue has been created: #${issueObj.number} - ${issueObj.title || '(no title)'}
Please prioritize this issue accordingly.

Best Regards,
Automated Notification System

${markerText}`;

    if (dryRun) {
      console.log(`DRY-RUN: Would comment on Issue #${issueObj.number} (${issueObj.html_url || 'no html_url in payload'}) with body:\n---\n${comment}\n---`);
      return true;
    }

    try {
      await githubClient.rest.issues. createComment({
        owner: ownerName,
        repo: repoName,
        issue_number: issueObj.number,
        body: comment,
      });
      console.log(`Notified team about P0 issue #${issueObj.number}`);
      return true;
    } catch (commentErr) {
      console.log(`Failed to notify team about P0 issue #${issueObj.number}:`, commentErr.message || commentErr);
      return false;
    }
  }

  // Execution flow

  // Check for existing bot comment first (be conservative on error)
  const existingBotComment = await hasExistingBotComment(github, owner, repo, issue, marker);
  if (existingBotComment) {
    console.log(`A P0 notification comment already exists (or comment-check failed) on Issue #${issue.number}. No duplicate comment posted. `);
    return;
  }

  const labels = await resolveIssueLabels(github, owner, repo, issue);
  const hasP0Label = Array.isArray(labels) && labels.some(label => (label && label.name && label.name. toLowerCase()) === 'p0');

  if (!hasP0Label) {
    console.log(`Issue #${issue.number} does not have the 'P0' label. No notification posted.`);
    return;
  }

  // Post the notification comment
  await postNotifyP0IssueComment(github, owner, repo, issue, marker);

  // Summary logs — show label names
  const labelNames = Array.isArray(labels) ? labels.map(l => l && l.name).filter(Boolean) : [];
  console.log('=== Summary ===');
  console.log(`Repository: ${owner}/${repo}`);
  console.log(`Issue Number: ${issue.number}`);
  console.log(`Issue Title: ${issue.title || '(no title)'}`);
  console.log(`Labels: ${labelNames.join(', ')}`);
};