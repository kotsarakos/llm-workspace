<script lang="ts">
	export let title = '';
	export let first = false;
	export let className = '';
</script>

<section class="llmw-card w-full {first ? '' : 'mt-4'} {className}">
	{#if title}
		<h3 class="llmw-section-title mb-2 text-xs text-base-600 dark:text-base-400">
			{title}
		</h3>
	{/if}

	<div class="llmw-card-body flex flex-col gap-2.5">
		<slot />
	</div>
</section>
