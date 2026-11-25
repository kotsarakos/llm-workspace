<script lang="ts">
	export let title = '';
	export let first = false;
	export let className = '';
</script>

<section class="llmw-card {first ? '' : 'mt-5'} {className}">
	{#if title}
		<h3 class="llmw-section-title mb-2 text-xs text-base-400 dark:text-base-600">
			{title}
		</h3>
	{/if}

	<div class="llmw-card-body flex flex-col gap-2.5">
		<slot />
	</div>
</section>
