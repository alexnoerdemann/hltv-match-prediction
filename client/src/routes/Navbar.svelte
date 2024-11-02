<nav class="navbar is-primary is-fixed-top" aria-label="main navigation">
  <div class="navbar-brand">
    <a href="#top" aria-label="Back to top"><img src="/favicon-96x96.png" alt="Back to top"></a>    
  </div>
  <div class="navbar-end">
    <div class="navbar-item">
      <div class="field">
        <p class="control has-icons-right">
          <input class="input is-rounded" type="text" placeholder="Match URL here" />
          <span class="icon is-small is-right">
            <i class="fa-solid fa-magnifying-glass"></i>
          </span>
        </p>
      </div>
    </div>
  </div>
</nav>

<style lang="scss">
  @use "bulma/sass/form/shared" with ($input-border-l-delta: 100%, $input-hover-border-l-delta: 100%, $input-active-border-l-delta: 100%, $input-icon-focus-color: $hmp-secondary-1);

  @forward "bulma/sass/components/navbar";
  @forward "bulma/sass/elements/icon";
  @forward "bulma/sass/form/input-textarea";
  @forward "bulma/sass/form/tools";
</style>