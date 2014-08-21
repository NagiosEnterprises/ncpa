## So You Want To Contribute?

Fantastic! Thats great news. Here is the skinny on how to contribute to this project.

### Make Your Own Repo

Clearly, you're probably familiar with making your own repo with this same source code. Go ahead and do that. Make
your changes. Test them to make sure they work! We absolutely will not accept anything that doesn't pass muster. 
Wondering what will pass muster? Here are a few things we will look for:

##### Is it PEP8?

Clearly, this nitpicky, but it is a requirement. So please, follow PEP8 to the closest you possibly can. We can
fix minor items that don't abide by PEP8, but please make it close.

##### Does it pass the tests?

Any merge that will be accepted *absolutely must* pass the following tests:

```
git pull <your repo> your-repo
cd ncpa-branch-pull
git checkout <your dev branch>
python run_tests.py agent/ client/
```

If it does not pass this, we will not merge the pull request. So please, run these tests before submitting your pull
request!

##### Is the change intelligible?

Does the change you pushed make sense? WE LOVE code that is functional, and we will definitely work with pull requests
that are functional but might be questionable in implementation. So please, even if you feel your change is a one-off
or not proper, submit it for review! We want the code to be proper and maintainable just as you. We will work with
any change that is movement towards something that makes the software fit the needs of the user better.

### Making Sure Your Changes Merge

Since you took the time to change the code, its going to be a lot easier for you to ensure the code merges properly.
Otherwise, someone who isn't familiar with your changes might make the changes and be caught in an awkward situation.
We'll just assume your repo is called ```<your repo>``` and you're done all work on your ```development``` branch.
Please run the following, and if a merge conflict pops up, note it in the pull request.

```
cd <your ncpa repo>
git checkout development
python run_tests.py agent/ client/ # This better pass!
git add remote upstream https://github.com/NagiosEnterprises/ncpa
git merge upstream/development
```

### Send Us A Pull Request

Send it! Wooo!

