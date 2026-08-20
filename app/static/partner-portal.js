document.addEventListener('DOMContentLoaded', () => {
  const escapeHtml = value => String(value ?? '').replace(
    /[&<>'"]/g,
    character => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[character]),
  );

  const dashboardSearch = document.getElementById('dashboard-customer-search');
  const dashboardResults = document.getElementById('dashboard-customer-results');
  if (dashboardSearch && dashboardResults) {
    let dashboardTimer;
    dashboardSearch.addEventListener('input', () => {
      clearTimeout(dashboardTimer);
      const query = dashboardSearch.value.trim();
      if (query.length < 2) {
        dashboardResults.classList.add('d-none');
        dashboardResults.innerHTML = '';
        return;
      }
      dashboardTimer = setTimeout(async () => {
        try {
          const response = await fetch(`/partner/customers/search?q=${encodeURIComponent(query)}`);
          if (!response.ok) throw new Error('Customer search failed');
          const data = await response.json();
          dashboardResults.innerHTML = data.results.length ? data.results.map(item => {
            const details = [item.phone, item.email, item.address].filter(Boolean).join(' · ');
            const platypus = item.platypus_account ? `Platypus ${item.platypus_account}` : item.number;
            return `<button type="button" class="customer-result dashboard-customer-result" data-id="${item.id}"><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(platypus)}</small><small>${escapeHtml(details || 'Active customer')}</small></button>`;
          }).join('') : '<div class="p-3 text-muted">No matching active customers.</div>';
          dashboardResults.classList.remove('d-none');
        } catch (_error) {
          dashboardResults.innerHTML = '<div class="p-3 text-danger">Customer search is temporarily unavailable.</div>';
          dashboardResults.classList.remove('d-none');
        }
      }, 250);
    });
    dashboardResults.addEventListener('click', event => {
      const customer = event.target.closest('[data-id]');
      if (customer) window.location.assign(`/partner?customer_id=${customer.dataset.id}`);
    });
    dashboardSearch.addEventListener('keydown', event => {
      if (event.key === 'Escape') dashboardResults.classList.add('d-none');
    });
    document.addEventListener('click', event => {
      if (!event.target.closest('.dashboard-search-wrap')) dashboardResults.classList.add('d-none');
    });
  }

  const search = document.getElementById('customer-search');
  if (!search) return;

  const results = document.getElementById('customer-results');
  const customerId = document.getElementById('customer-id');
  const selected = document.getElementById('selected-customer');
  const selectedContext = document.getElementById('selected-customer-context');
  const options = document.getElementById('customer-options');
  const submit = document.getElementById('submit-ticket');
  const contact = document.getElementById('contact-id');
  const location = document.getElementById('location-id');
  const service = document.getElementById('service-id');
  const contactDetails = document.getElementById('selected-contact-details');
  let timer;

  const fill = (select, items, label) => {
    if (!select) return;
    select.innerHTML = '<option value="">Not specified</option>' + items.map(
      item => `<option value="${item.id}">${escapeHtml(label(item))}</option>`,
    ).join('');
  };
  const chooseCustomer = data => {
    customerId.value = data.id;
    search.value = data.name;
    selected.innerHTML = `<strong>${escapeHtml(data.name)}</strong><span class="d-block small text-muted">${escapeHtml(data.number)}</span>`;
    selected.classList.remove('d-none');
    results.classList.add('d-none');
    contact.innerHTML = '<option value="">Not specified</option>' + data.contacts.map(
      item => `<option value="${item.id}" data-email="${escapeHtml(item.email)}" data-office="${escapeHtml(item.office)}" data-mobile="${escapeHtml(item.mobile)}" data-primary="${item.primary ? 'true' : 'false'}">${escapeHtml(item.name)}${item.primary ? ' · Primary' : ''}</option>`,
    ).join('');
    const primary = [...contact.options].find(option => option.dataset.primary === 'true');
    if (primary) contact.value = primary.value;
    location.innerHTML = '<option value="">Not specified</option>' + data.locations.map(
      item => `<option value="${item.id}" data-primary="${item.primary ? 'true' : 'false'}">${escapeHtml(item.name)}${item.address ? ' — ' + escapeHtml(item.address) : ''}${item.primary ? ' · Primary' : ''}</option>`,
    ).join('');
    const primaryLocation = [...location.options].find(option => option.dataset.primary === 'true');
    if (primaryLocation) location.value = primaryLocation.value;
    fill(service, data.services, item => item.name);
    if (options) options.classList.remove('d-none');
    submit.disabled = false;
    refreshContactDetails();
    if (selectedContext) {
      const billing = data.billing_contact || {};
      const serviceLocation = data.primary_service_location || {};
      const billingAddress = billing.address && billing.address_differs
        ? `<div><i class="fa-solid fa-file-invoice me-2"></i><span><small>Billing address</small>${escapeHtml(billing.address)}</span></div>` : '';
      selectedContext.innerHTML = `<section><strong>Billing Contact</strong><div><i class="fa-solid fa-user me-2"></i><span>${escapeHtml(billing.name || 'Not set')}</span></div><div><i class="fa-solid fa-phone me-2"></i><span>${escapeHtml(billing.phone || 'Not set')}</span></div><div><i class="fa-solid fa-envelope me-2"></i><span>${escapeHtml(billing.email || 'Not set')}</span></div>${billingAddress}</section><section><strong>Primary Service Location</strong><div><i class="fa-solid fa-location-dot me-2"></i><span><small>${escapeHtml(serviceLocation.name || 'Primary location')}</small>${escapeHtml(serviceLocation.address || 'No service address on account')}</span></div></section>`;
      selectedContext.classList.remove('d-none');
    }
  };

  const refreshContactDetails = () => {
    if (!contactDetails) return;
    const choice = contact.selectedOptions[0];
    if (!choice || !choice.value) {
      contactDetails.innerHTML = '<span class="text-muted">No contact selected.</span>';
      return;
    }
    const email = choice.dataset.email || '';
    const office = choice.dataset.office || '';
    const mobile = choice.dataset.mobile || '';
    const phone = office || mobile;
    contactDetails.innerHTML = `<div class="fw-semibold mb-1">${escapeHtml(choice.textContent.trim())}</div><div><i class="fa-solid fa-envelope me-2 text-muted"></i>${email ? `<a href="mailto:${escapeHtml(email)}">${escapeHtml(email)}</a>` : '<span class="text-danger">No email on account</span>'}</div><div><i class="fa-solid fa-phone me-2 text-muted"></i>${phone ? `<a href="tel:${escapeHtml(phone)}">${escapeHtml(phone)}</a>` : '<span class="text-danger">No phone number on account</span>'}</div>`;
  };

  search.addEventListener('input', () => {
    clearTimeout(timer);
    customerId.value = '';
    submit.disabled = true;
    selected.classList.add('d-none');
    if (selectedContext) selectedContext.classList.add('d-none');
    if (options) options.classList.add('d-none');
    const query = search.value.trim();
    if (query.length < 2) {
      results.classList.add('d-none');
      return;
    }
    timer = setTimeout(async () => {
      const response = await fetch(`/partner/customers/search?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      results.innerHTML = data.results.length ? data.results.map(item => {
        const places = item.locations.map(value => [value.city, value.state].filter(Boolean).join(', ')).join(' · ');
        const platypus = item.platypus_account ? ` · Platypus ${item.platypus_account}` : '';
        return `<button type="button" class="customer-result" data-id="${item.id}"><strong>${escapeHtml(item.name)} <small>${escapeHtml(item.number + platypus)}</small></strong><small>${escapeHtml(places || item.address || 'Active customer')}</small></button>`;
      }).join('') : '<div class="p-3 text-muted">No matching active customers.</div>';
      results.classList.remove('d-none');
    }, 250);
  });

  results.addEventListener('click', async event => {
    const button = event.target.closest('[data-id]');
    if (!button) return;
    const response = await fetch(`/partner/customers/${button.dataset.id}/options`);
    if (response.ok) chooseCustomer(await response.json());
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('.search-wrap')) results.classList.add('d-none');
  });

  contact.addEventListener('change', refreshContactDetails);
  const affectedService = document.getElementById('affected-service');
  const ticketType = document.getElementById('ticket-type');
  const refreshIssues = () => {
    let first = '';
    [...ticketType.options].forEach(option => {
      const visible = option.dataset.category === affectedService.value;
      option.hidden = !visible; option.disabled = !visible;
      if (visible && !first) first = option.value;
    });
    if (!ticketType.value || ticketType.selectedOptions[0]?.disabled) ticketType.value = first;
  };
  affectedService.addEventListener('change', refreshIssues); refreshIssues();

  const correspondenceMode = document.getElementById('correspondence-mode');
  const additionalCorrespondence = document.getElementById('additional-correspondence');
  const verificationStatus = document.getElementById('verification-status');
  const syncCorrespondence = () => additionalCorrespondence.classList.toggle('d-none', correspondenceMode.value !== 'additional');
  correspondenceMode.addEventListener('change', syncCorrespondence); syncCorrespondence();
  const resetVerification = channel => {
    document.getElementById(`correspondence-${channel}-verification-id`).value = '';
    document.getElementById(`${channel}-confirmation-group`).classList.add('d-none');
  };
  ['email', 'mobile'].forEach(channel => document.getElementById(`correspondence-${channel}`).addEventListener('input', () => resetVerification(channel)));
  const checkVerification = async channel => {
    const destination = document.getElementById(`correspondence-${channel}`);
    const verificationId = document.getElementById(`correspondence-${channel}-verification-id`);
    const state = document.getElementById(`${channel}-confirmation-state`);
    const data = new FormData(); data.set('verification_id', verificationId.value); data.set('customer_id', customerId.value); data.set('destination', destination.value.trim());
    try {
      const response = await fetch(`/partner/contact-verification/${channel}/status`, {method: 'POST', body: data});
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'Unable to check confirmation.');
      if (result.confirmed) {
        state.className = 'small text-success fw-semibold ms-2'; state.textContent = 'Received and confirmed';
        verificationStatus.className = 'alert alert-success py-2 small'; verificationStatus.textContent = `${result.destination} has been confirmed.`;
        return true;
      }
      state.textContent = result.status === 'expired' ? 'Confirmation expired' : 'Waiting for recipient';
    } catch (error) {
      verificationStatus.className = 'alert alert-danger py-2 small'; verificationStatus.textContent = error.message;
      return true;
    }
    return false;
  };
  document.querySelectorAll('.verification-check').forEach(button => button.addEventListener('click', () => checkVerification(button.dataset.channel)));
  document.querySelectorAll('.verification-send').forEach(button => button.addEventListener('click', async () => {
    const channel = button.dataset.channel;
    const destination = document.getElementById(`correspondence-${channel}`).value.trim();
    if (!customerId.value || !destination) {
      verificationStatus.className = 'alert alert-danger py-2 small'; verificationStatus.textContent = 'Select a customer and enter the destination first.'; return;
    }
    button.disabled = true; button.textContent = 'Sending…';
    const data = new FormData(); data.set('customer_id', customerId.value); data.set('channel', channel); data.set('destination', destination);
    try {
      const response = await fetch('/partner/contact-verification/send', {method: 'POST', body: data});
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'Unable to send verification.');
      document.getElementById(`correspondence-${channel}-verification-id`).value = result.verification_id;
      document.getElementById(`${channel}-confirmation-group`).classList.remove('d-none');
      verificationStatus.className = 'alert alert-success py-2 small'; verificationStatus.textContent = result.message;
      setTimeout(async function poll() { if (!(await checkVerification(channel))) setTimeout(poll, 5000); }, 5000);
    } catch (error) {
      verificationStatus.className = 'alert alert-danger py-2 small'; verificationStatus.textContent = error.message;
    } finally { button.disabled = false; button.textContent = 'Send verification'; }
  }));

  if (window.partnerInitialCustomer) chooseCustomer(window.partnerInitialCustomer);
});
