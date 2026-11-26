<!--
	Toast with a burning-fuse Undo button. The action is only committed when the
	fuse runs out; pressing Undo cancels it, so nothing has to be reverted.
	Show with: toast.custom(UndoToast, { componentProps: { message, onCommit }, unstyled: true })
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import FuseButton from '$lib/components/svelte-bits/FuseButton.svelte';
	import { isDarkMode } from '$lib/components/svelte-bits/theme';

	let {
		message,
		onCommit,
		onUndo = () => {},
		undoWindow = 4000,
		actionLabel = 'Archive',
		undoLabel = 'Undo',
		doneLabel = 'Done'
	}: {
		message: string;
		onCommit: () => void;
		onUndo?: () => void;
		undoWindow?: number;
		actionLabel?: string;
		undoLabel?: string;
		doneLabel?: string;
	} = $props();

	let root: HTMLDivElement;
	let state = $state<'pending' | 'undone' | 'done'>('pending');

	onMount(() => {
		// Start the fuse straight away: the user already chose the action.
		root.querySelector<HTMLButtonElement>('button')?.click();
	});
</script>

<div
	bind:this={root}
	data-toast-custom
	class="flex w-full items-center gap-3 rounded-2xl border border-violet-500/25 bg-base-0 px-3 py-2 text-[0.8125rem] text-base-800 shadow-lg shadow-violet-500/10 dark:bg-base-850 dark:text-base-100"
>
	<span class="flex-1">
		{state === 'undone' ? 'Cancelled' : state === 'done' ? `${message} ✓` : `${message}…`}
	</span>
	<FuseButton
		label={actionLabel}
		{undoLabel}
		{doneLabel}
		{undoWindow}
		commitOn="fuseEnd"
		settle="stay"
		size="sm"
		color={$isDarkMode ? '#ede9fe' : '#4c1d95'}
		background={$isDarkMode ? 'rgba(139, 92, 246, 0.18)' : 'rgba(139, 92, 246, 0.12)'}
		fuseColor="#a78bfa"
		onCommit={() => {
			state = 'done';
			onCommit();
		}}
		onUndo={() => {
			state = 'undone';
			onUndo();
		}}
	/>
</div>
