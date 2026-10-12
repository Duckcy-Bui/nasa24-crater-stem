# Đưa repo công khai lên GitHub

Tài khoản: `Duckcy-Bui`. Tên dự kiến: `nasa24-crater-stem`.

## 1. Tạo repo trên web

Đăng nhập đúng tài khoản, mở https://github.com/new, điền tên trên và chọn Public. Để README, .gitignore và license trống vì khung local đã có nội dung. Nhấn Create repository.

GitHub chỉ được coi là đã tạo khi bạn thấy trang repo. Nếu tên đã tồn tại, kiểm tra repo đó trước; không đẩy đè hoặc force push.

## 2. Push commit đã chuẩn bị

Repo local đã có nhánh main, commit đầu tiên và origin trỏ tới địa chỉ dự kiến. Từ Terminal:

```bash
cd /home/duckcy/work/XLA/nasa24-crater-stem
git remote -v
git push -u origin main
```

Lệnh push cần tài khoản GitHub đã xác thực trên máy. Nếu dùng HTTPS và Git yêu cầu mật khẩu, dùng cơ chế xác thực GitHub/PAT của bạn; không dùng mật khẩu đăng nhập thường và không ghi token vào repo hoặc lệnh lưu trong tài liệu.

Theo [hướng dẫn đưa code local lên GitHub](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).

## 3. Mời thành viên

Trong repo, vào Settings → Collaborators → Add people. Thêm username GitHub của Tiến, Hưng và Quốc Anh, rồi nhờ từng người nhận lời mời. Repo Public cho phép xem; để push nhánh trực tiếp, thành viên cần quyền cộng tác.

Theo [hướng dẫn mời cộng tác viên](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository).

## 4. Thành viên bắt đầu làm

Sau khi repo đã được tạo và có commit:

```bash
git clone https://github.com/Duckcy-Bui/nasa24-crater-stem.git
cd nasa24-crater-stem
git switch -c s1-07-hough-numpy
python3 scripts/check_contracts.py
```

Hưng đổi tên nhánh thành `s1-08-preprocessing`; Quốc Anh dùng `s1-06-data`. Khi có kết quả, kiểm tra thay đổi, commit các file liên quan, push nhánh rồi mở Pull Request.

```bash
git status
git add src/hough.py
git commit -m "S1-07: implement basic circular Hough"
git push -u origin s1-07-hough-numpy
```

Lệnh ví dụ này dùng cho phần của Tiến sau khi đã viết code; mỗi người thay file và mã việc đúng phần mình.

## 5. Ghi nhận S1-05

Sau khi push và các thành viên xác nhận chuẩn dữ liệu, đặt link repo vào `Giao_viec!O12`, cập nhật trạng thái tại `J12`. Hiện khung local chỉ là phần chuẩn bị; checklist còn trong `PHAN_CONG.md`.
