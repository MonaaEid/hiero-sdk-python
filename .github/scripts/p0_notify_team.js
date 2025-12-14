// Script to notify the team when a P0 issue is created. 
const customPayload = process.env.CUSTOM_PAYLOAD ? JSON.parse(process.env.CUSTOM_PAYLOAD) : null;

  // Helper: resolve labels for an issue — prefer payload labels, otherwise fetch from the API. 
  async function resolveIssueLabels(github, owner, repo, issue) {
    try {
      if (Array.isArray(issue.labels) && issue.labels.length > 0) {
        console.log(`Using labels from payload for Issue #${issue. number}`);
        return issue.labels;
      }

      console.log(`Fetching labels from API for Issue #${issue. number}`);
      const labels = await github.paginate(github.rest.issues. listLabelsOnIssue, {
        owner: owner,
        repo: repo,
        issue_number: issue. number,
        per_page: 100,
      });

      return Array.isArray(labels) ? labels : [];
    } catch (err) {
      console.log(`Failed to resolve labels for Issue #${issue.number}:`, err.message || err);
      // Return empty array so callers can operate safely. 
      return [];
    }
  }

  // Check for an existing bot comment using our unique marker. 
  async function hasExistingBotComment(github, owner, repo, issue, marker) {
    try {
      const comments = await github.paginate(github.rest. issues.listComments, {
        owner: owner,
        repo: repo,
        issue_number: issue.number,
        per_page: 100,
      });
     return comments.find(c => c.body && c.body.includes(marker)) || false;
    } catch (err) {
      console.log(`Failed to list comments for Issue #${issue.number}:`, err.message || err);
      // Be conservative: if we cannot check comments, avoid posting to prevent duplicates.
      return null;
    }
  }

  async function postNotifyP0IssueComment(github, owner, repo, issue, marker) {
    const comment = `${marker} :rotating_light: Attention Team : rotating_light: 
@team-python-sdk/triage

A new P0 issue has been created: #${issue.number} - ${issue.title || '(no title)'}
Please prioritize this issue accordingly.

Best Regards,
Automated Notification System`;
if (customPayload) {
  console.log('CUSTOM PAYLOAD: would post comment on Issue #' + issue.number + ' (' + issue.html_url + ') with body:\n---\n' + comment + '\n---');
  return true;
}
    try {
      await github.rest.issues. createComment({
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

module.exports = async ({ github, context, customPayload = null }) => {
  const owner = context.repo && context.repo.owner;
  const repo = context.repo && context.repo.repo;
  const marker = '<!-- P0 Issue Notification -->';
  
  // Use custom payload if provided (for testing), otherwise use the real event payload
  const payload = customPayload || context.payload;
  const issue = payload && payload.issue;

  if (customPayload) {
    console.log('Using CUSTOM PAYLOAD for testing');
  }

  // Early return if no issue in payload
  if (! issue || typeof issue. number === 'undefined') {
    console.log('No issue found in the event payload.  Nothing to do.');
    return;
  }

  // Fast-fail for "labeled" events that aren't the P0 label
  const action = payload && payload.action;
  if (action === 'labeled') {
    const label = payload. label;
    if (! label || (label.name || '').toLowerCase() !== 'p0') {
      console.log(`Issue #${issue.number} was labeled with '${label ?  label.name : 'unknown'}' — not 'p0'.  Exiting. `);
      return;
    }
  }

  // Execution flow

  // Check for existing bot comment first (be conservative on error)
  const existingBotComment = await hasExistingBotComment(github, owner, repo, issue, marker);
  if (existingBotComment) {
    console.log(`A P0 notification comment already exists (or comment-check failed) on Issue #${issue.number}. No duplicate comment posted.`);
    return;
  }

  const labels = await resolveIssueLabels(github, owner, repo, issue);
  const hasP0Label = Array.isArray(labels) && labels.some(label => (label && label.name && label.name.toLowerCase()) === 'p0');

  if (! hasP0Label) {
    console.log(`Issue #${issue.number} does not have the 'P0' label. No notification posted. `);
    return;
  }

  // Post the notification comment
  await postNotifyP0IssueComment(github, owner, repo, issue, marker);

  // Summary logs — show label names
  const labelNames = Array. isArray(labels) ? labels.map(l => l && l. name).filter(Boolean) : [];
  console.log('=== Summary ===');
  console.log(`Repository: ${owner}/${repo}`);
  console.log(`Issue Number: ${issue.number}`);
  console.log(`Issue Title: ${issue.title || '(no title)'}`);
  console.log(`Labels: ${labelNames.join(', ')}`);
};