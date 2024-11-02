<script>
  import Navbar from './Navbar.svelte';
</script>

<div class="body-content">    
  <Navbar></Navbar>

  <section class="hero is-info is-fullheight">
    <div class="hero-body">
      <div class="container has-text-centered">
        <h1 class="title is-1">HLTV Match Prediction</h1>
        <h2 class="subtitle is-2">HMP</h2>
        <p>For the match prediction insert the <b>match URL</b> into the <b>search bar</b> and ... Well not much will happen yet. WIP.</p>
      </div>
    </div>
  </section>

  <footer class="footer">
  <div class="content has-text-centered">
    <p>
      <b><a href="https://github.com/alexnoerdemann/hltv-match-prediction">HMP</a></b> by <b><a href="https://github.com/alexnoerdemann">Alex Nördemann</a></b>.
      Free and open source released under the
      <b><a href="https://github.com/gogs/gogs/blob/main/conf/license/GNU%20General%20Public%20License%20v3.0">GPL-3.0</a></b> license.
    </p>
  </div>
</footer>
</div>

<style lang="scss">
  @forward "bulma/sass/elements/title";
  @forward "bulma/sass/helpers/typography";
  @forward "bulma/sass/layout/container";
  @forward "bulma/sass/layout/footer" with ($footer-background-color: $hmp-dark-neutral);
  @forward "bulma/sass/layout/hero";

  .body-content {
      background-color: $hmp-neutral;
      height: 100vh;
  }
</style>
